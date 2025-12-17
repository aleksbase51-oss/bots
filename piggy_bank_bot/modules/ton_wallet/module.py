import logging
from aiogram import Router, types
from aiogram.filters import Command, CommandObject, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from decimal import Decimal
from datetime import datetime

from .ton_service import TONService
from .repository import WalletRepository
from shared.config import config
from core.module_manager import register_module


logger = logging.getLogger(__name__)
router = Router()

# Состояния FSM
class WalletStates(StatesGroup):
    waiting_for_address = State()
    waiting_for_name = State()


def get_main_keyboard():
    """Основная клавиатура модуля"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Баланс"), KeyboardButton(text="👛 Кошельки")],
            [KeyboardButton(text="➕ Добавить"), KeyboardButton(text="❌ Удалить")]
        ],
        resize_keyboard=True
    )


@router.message(Command("wallet", "кошелек"))
async def cmd_wallet(message: Message):
    """Главная команда модуля кошельков"""
    text = (
        "👛 *TON Кошельки*\n\n"
        "Команды:\n"
        "• /connect_wallet - Привязать кошелек\n"
        "• /my_wallets - Список кошельков\n"
        "• /balance - Проверить баланс\n"
        "• /remove_wallet - Удалить кошелек"
    )
    
    await message.answer(text, parse_mode="Markdown", reply_markup=get_main_keyboard())


@router.message(Command("connect_wallet"))
@router.message(lambda message: message.text and message.text in ["➕ Добавить", "➕ Добавить кошелек"])
async def cmd_connect_wallet(message: Message, state: FSMContext, command: CommandObject = None):
    """Привязать новый кошелек"""
    if command and command.args:
        # Если адрес передан как аргумент команды
        address = command.args.strip()
        await process_address(message, address, state)
    else:
        # Запрашиваем адрес
        await message.answer(
            "📝 *Введите адрес TON кошелька:*\n\n"
            "Формат: UQ... или EQ...\n"
            "Пример: UQATKnigdlBIuU3FJ57VSh4Aqxel9oLbQ4hBzIZ6YzWkbZys\n\n"
            "Можно отменить командой /cancel",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardRemove()
        )
        await state.set_state(WalletStates.waiting_for_address)


async def process_address(message: Message, address: str, state: FSMContext):
    """Обработка адреса кошелька"""
    # Простая проверка длины
    if len(address) < 20:
        await message.answer(
            "❌ Слишком короткий адрес!",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Проверяем начинается ли с UQ/EQ или содержит :
    if not (address.startswith(('UQ', 'EQ')) or ':' in address):
        await message.answer(
            "❌ *Неверный формат адреса!*\n\n"
            "Должен начинаться с UQ, EQ или быть в формате 0:xxxx...",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
        return
    
    # Сохраняем адрес
    await state.update_data(wallet_address=address)
    await message.answer(
        "✅ *Адрес принят!*\n\n"
        "Введите имя для кошелька (например: 'Основной'):\n"
        "Или /skip чтобы оставить без имени",
        parse_mode="Markdown"
    )
    await state.set_state(WalletStates.waiting_for_name)


@router.message(
    WalletStates.waiting_for_address,
    lambda message: message.text and message.text.strip() != "/cancel"
)
async def process_wallet_address(message: Message, state: FSMContext):
    """Обработка введенного адреса"""
    address = message.text.strip()
    await process_address(message, address, state)


@router.message(
    WalletStates.waiting_for_name,
    lambda message: message.text and message.text.strip() != "/cancel"
)
async def process_wallet_name(message: Message, state: FSMContext):
    """Обработка имени кошелька"""
    data = await state.get_data()
    address = data.get("wallet_address")
    
    friendly_name = message.text.strip() if message.text != "/skip" else None
    
    # Сохраняем в базу
    repo = WalletRepository()
    success = await repo.add_wallet(message.from_user.id, address, friendly_name)
    
    if success:
        # Укорачиваем адрес для отображения
        if len(address) > 25:
            display_addr = address[:12] + "..." + address[-8:]
        else:
            display_addr = address
        
        await message.answer(
            f"✅ *Кошелек добавлен!*\n\n"
            f"Адрес: `{display_addr}`\n"
            f"Имя: {friendly_name or 'Не указано'}\n\n"
            f"Используйте /balance для проверки баланса",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    else:
        await message.answer(
            "❌ *Кошелек уже привязан!*",
            parse_mode="Markdown",
            reply_markup=get_main_keyboard()
        )
    
    await state.clear()


@router.message(Command("my_wallets"))
@router.message(lambda message: message.text and message.text in ["👛 Кошельки", "👛 Мои кошельки"])
async def cmd_my_wallets(message: Message):
    """Список кошельков"""
    repo = WalletRepository()
    wallets = await repo.get_user_wallets(message.from_user.id)
    
    if not wallets:
        await message.answer(
            "📭 *Нет привязанных кошельков*\n"
            "Используйте /connect_wallet",
            parse_mode="Markdown"
        )
        return
    
    text = "👛 *Ваши кошельки:*\n\n"
    for i, wallet in enumerate(wallets, 1):
        name = wallet.friendly_name or "Без имени"
        addr = wallet.wallet_address
        short_addr = addr[:10] + "..." + addr[-5:]
        
        text += f"{i}. *{name}*\n"
        text += f"   `{short_addr}`\n\n"
    
    text += f"Всего: {len(wallets)} кошельков"
    
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("balance"))
@router.message(lambda message: message.text and message.text in ["📊 Баланс", "📊 Мой баланс"])
async def cmd_balance(message: Message):
    """Проверка баланса"""
    repo = WalletRepository()
    wallets = await repo.get_user_wallets(message.from_user.id)
    
    if not wallets:
        await message.answer(
            "📭 *Сначала привяжите кошелек*",
            parse_mode="Markdown"
        )
        return
    
    await message.answer("⏳ *Проверяю балансы...*", parse_mode="Markdown")
    
    total_ton = Decimal(0)
    total_spw = Decimal(0)
    text = "💎 *Балансы:*\n\n"
    has_data = False
    
    async with TONService(config.TON_API_KEY) as ton_service:
        for i, wallet in enumerate(wallets, 1):
            try:
                balances = await ton_service.get_wallet_balances(wallet.wallet_address)
                
                name = wallet.friendly_name or f"Кошелек {i}"
                short_addr = wallet.wallet_address[:8] + "..." + wallet.wallet_address[-4:]
                
                # Если оба баланса 0
                if balances['ton_balance'] == 0 and balances['spw_balance'] == 0:
                    text += f"*{name}* (`{short_addr}`)\n"
                    text += "Баланс: 0.00 TON, 0.00 SPW\n\n"
                else:
                    text += f"*{name}* (`{short_addr}`)\n"
                    text += f"TON: {balances['ton_human']}\n"
                    text += f"SPW: {balances['spw_human']}\n\n"
                    
                    total_ton += balances['ton_balance']
                    total_spw += balances['spw_balance']
                    has_data = True
                    
            except Exception as e:
                logger.error(f"Ошибка: {e}")
                text += f"*{wallet.friendly_name or f'Кошелек {i}'}* - ❌ Ошибка\n\n"
    
    if has_data:
        ton_total = ton_service.format_balance(total_ton, 9)
        spw_total = ton_service.format_balance(total_spw, 9)
        
        text += f"💰 *Итого:*\n"
        text += f"TON: *{ton_total}*\n"
        text += f"SPW: *{spw_total}*\n"
    
    text += f"\n_Обновлено: {datetime.now().strftime('%H:%M')}_"
    
    await message.answer(text, parse_mode="Markdown")


@router.message(Command("save_balance"))
async def cmd_save_balance(message: Message):
    """
    Сохранить текущие балансы всех кошельков в историю
    Используется для ручного сохранения статистики
    """
    repo = WalletRepository()
    wallets = await repo.get_user_wallets(message.from_user.id)
    
    if not wallets:
        await message.answer(
            "📭 *Сначала привяжите кошелек*",
            parse_mode="Markdown"
        )
        return
    
    await message.answer("⏳ *Получаю балансы и сохраняю в историю...*", parse_mode="Markdown")
    
    saved_count = 0
    failed_count = 0
    
    async with TONService(config.TON_API_KEY) as ton_service:
        for wallet in wallets:
            try:
                # Получаем текущие балансы
                balances = await ton_service.get_wallet_balances(wallet.wallet_address)
                
                # Сохраняем в историю
                success = await repo.save_balance_history(
                    telegram_id=message.from_user.id,
                    wallet_address=wallet.wallet_address,
                    ton_balance=balances['ton_balance'],
                    spw_balance=balances['spw_balance']
                )
                
                if success:
                    saved_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Ошибка сохранения баланса для {wallet.wallet_address}: {e}")
                failed_count += 1
    
    # Формируем сообщение о результате
    result_text = "✅ *Балансы сохранены в историю!*\n\n"
    result_text += f"Успешно: {saved_count} кошельков\n"
    
    if failed_count > 0:
        result_text += f"Ошибок: {failed_count}\n"
    
    result_text += f"\n_Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}_"
    
    await message.answer(result_text, parse_mode="Markdown")


@router.message(Command("remove_wallet"))
@router.message(lambda message: message.text and message.text in ["❌ Удалить", "❌ Удалить кошелек"])
async def cmd_remove_wallet(message: Message):
    """Удаление кошелька"""
    repo = WalletRepository()
    wallets = await repo.get_user_wallets(message.from_user.id)
    
    if not wallets:
        await message.answer("📭 *Нет кошельков для удаления*", parse_mode="Markdown")
        return
    
    # Создаем клавиатуру
    keyboard = []
    for wallet in wallets:
        name = wallet.friendly_name or wallet.wallet_address[:15] + "..."
        keyboard.append([KeyboardButton(text=f"🗑️ {name}")])
    
    keyboard.append([KeyboardButton(text="🔙 Назад")])
    
    markup = ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    
    await message.answer(
        "Выберите кошелек для удаления:",
        reply_markup=markup
    )


@router.message(lambda message: message.text and message.text.startswith("🗑️ "))
async def process_remove(message: Message):
    """Обработка удаления"""
    repo = WalletRepository()
    wallets = await repo.get_user_wallets(message.from_user.id)
    
    selected = message.text.replace("🗑️ ", "")
    
    for wallet in wallets:
        name = wallet.friendly_name or wallet.wallet_address[:15] + "..."
        if name == selected:
            success = await repo.remove_wallet(message.from_user.id, wallet.wallet_address)
            if success:
                await message.answer(f"✅ Кошелек '{name}' удален", reply_markup=get_main_keyboard())
            else:
                await message.answer("❌ Ошибка удаления", reply_markup=get_main_keyboard())
            return
    
    await message.answer("❌ Кошелек не найден", reply_markup=get_main_keyboard())


@router.message(lambda message: message.text and message.text == "🔙 Назад")
async def cmd_back(message: Message):
    """Назад в меню"""
    await message.answer("Меню:", reply_markup=get_main_keyboard())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущего действия"""
    current = await state.get_state()
    if current:
        await state.clear()
        await message.answer("❌ Действие отменено", reply_markup=get_main_keyboard())
    else:
        await message.answer("❌ Нет активных действий для отмены", reply_markup=get_main_keyboard())


# Регистрация модуля
module_info = {
    "name": "TON Кошельки",
    "description": "Привязка и отслеживание TON кошельков",
    "commands": {
        "/wallet": "Главное меню",
        "/connect_wallet [адрес]": "Привязать кошелек",
        "/my_wallets": "Мои кошельки",
        "/balance": "Балансы",
        "/save_balance": "Сохранить балансы в историю",
        "/remove_wallet": "Удалить кошелек",
        "/cancel": "Отмена"
    },
    "router": router
}

register_module(module_info)