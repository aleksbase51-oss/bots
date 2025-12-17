import logging
from typing import List, Optional
from datetime import datetime
from decimal import Decimal
from .models import Wallet, WalletBalanceHistory
from shared.database import db

logger = logging.getLogger(__name__)


class WalletRepository:
    def __init__(self):
        self.client = db.get_client()

    async def create_user(self, telegram_id: int, username: str = None) -> bool:
        """Создать нового пользователя"""
        try:
            # Проверяем существует ли уже пользователь
            existing = self.client.table("users") \
                .select("telegram_id") \
                .eq("telegram_id", telegram_id) \
                .execute()
            
            if existing.data:
                return True
            
            # Создаем нового пользователя
            user_data = {
                "telegram_id": telegram_id,
                "username": username,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("users").insert(user_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False

    async def add_wallet(self, telegram_id: int, wallet_address: str, friendly_name: str = None) -> bool:
        """Добавить кошелек пользователю"""
        try:
            # Сначала создаем пользователя если его нет
            await self.create_user(telegram_id, username=None)
            
            # Проверяем нет ли уже такого кошелька у пользователя
            existing = await self.wallet_exists(telegram_id, wallet_address)
            if existing:
                return False
            
            wallet_data = {
                "telegram_id": telegram_id,
                "wallet_address": wallet_address,
                "friendly_name": friendly_name,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("wallets").insert(wallet_data).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error adding wallet: {e}")
            return False

    async def get_user_wallets(self, telegram_id: int) -> List[Wallet]:
        """Получить все кошельки пользователя"""
        try:
            result = self.client.table("wallets") \
                .select("*") \
                .eq("telegram_id", telegram_id) \
                .order("created_at", desc=True) \
                .execute()
            
            wallets = []
            for row in result.data:
                wallet = Wallet(
                    id=row.get("id"),
                    telegram_id=row["telegram_id"],
                    wallet_address=row["wallet_address"],
                    friendly_name=row.get("friendly_name"),
                    created_at=datetime.fromisoformat(row["created_at"]) if row.get("created_at") else None
                )
                wallets.append(wallet)
            
            return wallets
        except Exception as e:
            logger.error(f"Error getting user wallets: {e}")
            return []

    async def remove_wallet(self, telegram_id: int, wallet_address: str) -> bool:
        """Удалить кошелек пользователя"""
        try:
            result = self.client.table("wallets") \
                .delete() \
                .eq("telegram_id", telegram_id) \
                .eq("wallet_address", wallet_address) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error removing wallet: {e}")
            return False

    async def wallet_exists(self, telegram_id: int, wallet_address: str) -> bool:
        """Проверить, существует ли уже такой кошелек у пользователя"""
        try:
            result = self.client.table("wallets") \
                .select("id") \
                .eq("telegram_id", telegram_id) \
                .eq("wallet_address", wallet_address) \
                .execute()
            
            return len(result.data) > 0
        except Exception:
            return False

    async def save_balance_history(self, telegram_id: int, wallet_address: str, 
                                   ton_balance: Decimal, spw_balance: Decimal) -> bool:
        """
        Сохранить текущий баланс кошелька в историю
        
        Args:
            telegram_id: ID пользователя в Telegram
            wallet_address: Адрес кошелька
            ton_balance: Баланс TON в нанотонах
            spw_balance: Баланс SPW в нанотокенах
            
        Returns:
            True если успешно сохранено, False если ошибка
        """
        try:
            # Подготавливаем данные для записи
            history_data = {
                "telegram_id": telegram_id,
                "wallet_address": wallet_address,
                "ton_balance": str(ton_balance),  # Преобразуем Decimal в строку для JSON
                "spw_balance": str(spw_balance),
                "recorded_at": datetime.now().isoformat()
            }
            
            # Сохраняем в таблицу wallet_balance_history
            result = self.client.table("wallet_balance_history").insert(history_data).execute()
            
            logger.info(f"Баланс сохранён в историю: {wallet_address[:10]}... TON={ton_balance}, SPW={spw_balance}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error saving balance history: {e}")
            return False

    async def get_balance_history(self, wallet_address: str, limit: int = 30) -> List[WalletBalanceHistory]:
        """
        Получить историю балансов кошелька
        
        Args:
            wallet_address: Адрес кошелька
            limit: Сколько последних записей вернуть (по умолчанию 30)
            
        Returns:
            Список записей истории балансов, отсортированный по дате (новые первые)
        """
        try:
            result = self.client.table("wallet_balance_history") \
                .select("*") \
                .eq("wallet_address", wallet_address) \
                .order("recorded_at", desc=True) \
                .limit(limit) \
                .execute()
            
            history = []
            for row in result.data:
                record = WalletBalanceHistory(
                    id=row.get("id"),
                    telegram_id=row.get("telegram_id"),
                    wallet_address=row["wallet_address"],
                    ton_balance=Decimal(row["ton_balance"]),
                    spw_balance=Decimal(row["spw_balance"]),
                    recorded_at=datetime.fromisoformat(row["recorded_at"])
                )
                history.append(record)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting balance history: {e}")
            return []

    async def get_user_balance_history(self, telegram_id: int, limit: int = 30) -> List[WalletBalanceHistory]:
        """
        Получить историю балансов всех кошельков пользователя
        
        Args:
            telegram_id: ID пользователя в Telegram
            limit: Сколько последних записей вернуть
            
        Returns:
            Список записей истории балансов всех кошельков пользователя
        """
        try:
            result = self.client.table("wallet_balance_history") \
                .select("*") \
                .eq("telegram_id", telegram_id) \
                .order("recorded_at", desc=True) \
                .limit(limit) \
                .execute()
            
            history = []
            for row in result.data:
                record = WalletBalanceHistory(
                    id=row.get("id"),
                    telegram_id=row.get("telegram_id"),
                    wallet_address=row["wallet_address"],
                    ton_balance=Decimal(row["ton_balance"]),
                    spw_balance=Decimal(row["spw_balance"]),
                    recorded_at=datetime.fromisoformat(row["recorded_at"])
                )
                history.append(record)
            
            return history
            
        except Exception as e:
            logger.error(f"Error getting user balance history: {e}")
            return []