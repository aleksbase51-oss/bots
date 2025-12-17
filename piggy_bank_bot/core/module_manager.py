# core/module_manager.py
import os
import importlib
from typing import Dict, Any

modules: Dict[str, Dict[str, Any]] = {}

def register_module(module_info: dict):
    """Регистрация модуля в системе"""
    module_name = module_info.get("name", "unknown")
    modules[module_name] = module_info
    print(f"📦 Модуль зарегистрирован: {module_name}")
    print(f"   Команды: {list(module_info.get('commands', {}).keys())}")  # Отладка

def get_all_commands() -> dict:
    """Получить все команды из всех модулей"""
    all_commands = {}
    for module_data in modules.values():
        if "commands" in module_data:
            all_commands.update(module_data["commands"])
    return all_commands

def get_all_routers():
    """Получить все роутеры модулей"""
    routers = []
    for module_data in modules.values():
        if "router" in module_data:
            routers.append(module_data["router"])
    return routers

def load_all_modules():
    """Автоматическая загрузка всех модулей"""
    modules_dir = "modules"
    if not os.path.exists(modules_dir):
        os.makedirs(modules_dir)
        print(f"📁 Создана папка для модулей: {modules_dir}")
        return
    
    for item in os.listdir(modules_dir):
        module_path = os.path.join(modules_dir, item)
        if os.path.isdir(module_path) and not item.startswith("__"):
            try:
                # ⭐️ Импортируем модуль
                module = importlib.import_module(f"modules.{item}")
                print(f"✅ Загружен модуль: {item}")
                
                # Проверяем, есть ли в модуле router
                if hasattr(module, 'router'):
                    print(f"   Найден router в {item}")
            except ImportError as e:
                print(f"⚠️ Модуль {item} не загружен: {e}")
            except Exception as e:
                print(f"❌ Ошибка загрузки модуля {item}: {e}")
    
    print(f"\n📊 Итог: зарегистрировано {len(modules)} модулей")
    print(f"Модули: {list(modules.keys())}")