# modules/start/start_module.py (60 строк)
from aiogram import Router, types
from aiogram.filters import Command
from core.module_manager import register_module, get_all_commands

router = Router()

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот 'Финансовая Копилка'.\n"
        "Используй /help для списка команд."
    )

@router.message(Command("help"))
async def cmd_help(message: types.Message):
    commands = get_all_commands()
    
    if not commands:
        help_text = "📭 Нет доступных команд."
    else:
        help_text = "📚 Доступные команды:\n\n"
        for command, description in commands.items():
            help_text += f"🔹 {command} - {description}\n"
    
    await message.answer(help_text)

# Регистрация модуля
module_info = {
    "name": "Старт",
    "commands": {
        "/start": "Начать работу",
        "/help": "Помощь"
    },
    "router": router
}

register_module(module_info)  # ⬅️ Этот вызов регистрирует модуль