import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from shared.config import config
from core.module_manager import load_all_modules, get_all_routers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_bot():
    """Запуск бота с загрузкой модулей"""
    # Проверка конфигурации
    config.validate()
    
    # Инициализация бота
    bot = Bot(token=config.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Загрузка всех модулей
    print("🔄 Загрузка модулей...")
    load_all_modules()
    
    # Регистрация роутеров из модулей
    routers = get_all_routers()
    for router in routers:
        dp.include_router(router)
    
    print(f"✅ Загружено модулей: {len(routers)}")
    print("🚀 Бот запущен! Нажмите Ctrl+C для остановки.")
    
    try:
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        print("👋 Бот остановлен")
    finally:
        await bot.session.close()

def start_bot():
    """Синхронный запуск бота"""
    asyncio.run(run_bot())