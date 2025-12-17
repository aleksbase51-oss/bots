from aiogram import Router, types
from aiogram.filters import Command
from core.module_manager import register_module

router = Router()

@router.message(Command("ranking"))
async def cmd_ranking(message: types.Message):
    await message.answer("🏆 Модуль рейтинга SPW держателей (в разработке)")

# Регистрация модуля
module_info = {
    "name": "SPW Рейтинг",
    "description": "Рейтинг держателей SPW токенов",
    "commands": {
        "/ranking": "Топ держателей SPW",
        "/myrank": "Мое место в рейтинге",
        "/spw_info": "Информация о SPW токене"
    },
    "router": router
}

register_module(module_info)