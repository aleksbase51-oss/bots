import aiohttp
import logging
import asyncio
import re
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime

logger = logging.getLogger(__name__)

# Константы
TON_API_BASE = "https://tonapi.io/v2"
# SPW токен адрес в raw формате (как возвращает API)
SPW_TOKEN_ADDRESS = "0:018bbd60d72dc1167c40fea718fa08926ed471f6002b03dc57a5f799c93a8ffc"
TON_DECIMALS = 9
SPW_DECIMALS = 9


class TONService:
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self.session = None
        self.headers = {"Accept": "application/json"}
        # Добавляем Authorization только если ключ есть и не пустой
        if api_key and api_key.strip():
            self.headers["Authorization"] = f"Bearer {api_key}"
            logger.info("TON API инициализирован с ключом")
        else:
            logger.info("TON API инициализирован БЕЗ ключа (публичный доступ)")

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(headers=self.headers)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_user_friendly_address(self, raw_address: str) -> str:
        """Конвертировать адрес в user-friendly формат (как в плагине)"""
        # Очищаем адрес от пробелов
        raw_address = raw_address.strip()
        
        # Если уже в правильном UQ/EQ формате - возвращаем как есть
        if re.match(r'^(UQ|EQ)[A-Za-z0-9_-]+$', raw_address):
            return raw_address
        
        # Если адрес в raw формате (0:hash или -1:hash), конвертируем через API
        try:
            # Проверяем наличие сессии, если нет - создаём временную
            if self.session is None:
                async with aiohttp.ClientSession(headers=self.headers) as temp_session:
                    parse_url = f"{TON_API_BASE}/address/{raw_address}/parse"
                    async with temp_session.get(parse_url, timeout=15) as response:
                        if response.status == 200:
                            parse_data = await response.json()
                            # API возвращает адрес в поле b64url УЖЕ с префиксом UQ/EQ
                            if parse_data.get("non_bounceable", {}).get("b64url"):
                                return parse_data["non_bounceable"]["b64url"]
            else:
                # Используем существующую сессию
                parse_url = f"{TON_API_BASE}/address/{raw_address}/parse"
                async with self.session.get(parse_url, timeout=15) as response:
                    if response.status == 200:
                        parse_data = await response.json()
                        # API возвращает адрес в поле b64url УЖЕ с префиксом UQ/EQ
                        if parse_data.get("non_bounceable", {}).get("b64url"):
                            return parse_data["non_bounceable"]["b64url"]
                        
        except asyncio.TimeoutError:
            logger.error(f"Timeout converting address: {raw_address}")
        except Exception as e:
            logger.error(f"Error converting address: {raw_address}: {type(e).__name__}: {str(e)}")
        
        # Если конвертация не удалась, возвращаем исходный адрес
        return raw_address

    async def get_ton_balance(self, address: str) -> Decimal:
        """Получить баланс TON в нанотонах"""
        try:
            friendly_address = await self.get_user_friendly_address(address)
            logger.info(f"Getting TON balance for: {address} -> {friendly_address}")
            
            url = f"{TON_API_BASE}/accounts/{friendly_address}"
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    balance = Decimal(data.get("balance", 0))
                    logger.info(f"TON balance: {balance}")
                    return balance
                else:
                    logger.warning(f"TON API error {response.status} for {address}")
                    return Decimal(0)
        except Exception as e:
            logger.error(f"Error getting TON balance for {address}: {type(e).__name__}: {str(e)}", exc_info=True)
            return Decimal(0)

    async def get_spw_balance(self, address: str) -> Decimal:
        """Получить баланс SPW токена"""
        try:
            friendly_address = await self.get_user_friendly_address(address)
            logger.info(f"Getting SPW balance for: {address} -> {friendly_address}")
            
            # Получаем балансы всех токенов
            url = f"{TON_API_BASE}/accounts/{friendly_address}/jettons"
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Логируем все найденные токены для отладки
                    logger.info(f"Found {len(data.get('balances', []))} jettons in wallet")
                    for jetton in data.get("balances", []):
                        jetton_info = jetton.get("jetton", {})
                        jetton_address = jetton_info.get("address", "")
                        jetton_name = jetton_info.get("name", "Unknown")
                        jetton_symbol = jetton_info.get("symbol", "?")
                        balance = jetton.get("balance", 0)
                        logger.info(f"  - {jetton_symbol} ({jetton_name}): {balance} | Address: {jetton_address}")
                    
                    # Ищем SPW токен по адресу токена
                    for jetton in data.get("balances", []):
                        jetton_info = jetton.get("jetton", {})
                        jetton_address = jetton_info.get("address", "")
                        
                        if jetton_address == SPW_TOKEN_ADDRESS:
                            balance = Decimal(jetton.get("balance", 0))
                            logger.info(f"SPW balance found: {balance}")
                            return balance
                    
                    logger.info(f"SPW token not found. Looking for: {SPW_TOKEN_ADDRESS}")
                    return Decimal(0)  # SPW не найден
                else:
                    logger.warning(f"TON API jetsons error {response.status}")
                    return Decimal(0)
        except Exception as e:
            logger.error(f"Error getting SPW balance for {address}: {type(e).__name__}: {str(e)}", exc_info=True)
            return Decimal(0)

    def format_balance(self, balance: Decimal, decimals: int) -> str:
        """Форматировать баланс для отображения"""
        if balance == 0:
            return "0.00"
        
        human_balance = balance / Decimal(10 ** decimals)
        # Форматируем с двумя знаками после запятой
        formatted = f"{human_balance:,.2f}"
        # Заменяем запятые на пробелы для тысяч
        return formatted.replace(',', ' ')

    async def get_wallet_balances(self, address: str) -> Dict[str, Any]:
        """Получить все балансы кошелька"""
        try:
            # Получаем оба баланса (можно последовательно, чтобы проще было)
            ton_balance = await self.get_ton_balance(address)
            spw_balance = await self.get_spw_balance(address)
            
            return {
                "ton_balance": ton_balance,
                "spw_balance": spw_balance,
                "ton_human": self.format_balance(ton_balance, TON_DECIMALS),
                "spw_human": self.format_balance(spw_balance, SPW_DECIMALS),
                "address": address,
                "last_updated": datetime.now()
            }
        except Exception as e:
            logger.error(f"Error getting wallet balances: {e}")
            # Возвращаем нули при ошибке
            return {
                "ton_balance": Decimal(0),
                "spw_balance": Decimal(0),
                "ton_human": "0.00",
                "spw_human": "0.00",
                "address": address,
                "last_updated": datetime.now()
            }

    def is_valid_address_format(self, address: str) -> bool:
        """Проверка только формата адреса (без API)"""
        address = address.strip()
        
        # 1. User-friendly форматы (UQ/EQ)
        if re.match(r'^(UQ|EQ)[A-Za-z0-9_-]{40,}$', address):
            return True
        
        # 2. Raw адрес (workchain:hash)
        if re.match(r'^(-?[0-9]+):[a-fA-F0-9]{64}$', address):
            return True
        
        # 3. Базовый адрес (простая проверка длины)
        if len(address) >= 40 and address.isalnum():
            return True
        
        return False


# Аналог is_wp_error из плагина (упрощенный)
def is_http_error(response_status: int) -> bool:
    """Проверка на ошибку HTTP"""
    return response_status >= 400