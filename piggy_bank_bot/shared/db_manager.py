# shared/db_manager.py
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.db_type = None
        self.db = None
        self.init_database()
    
    def init_database(self):
        """Инициализировать базу данных (выбирает тип автоматически)"""
        try:
            # Пробуем использовать локальную базу
            from shared.local_database import local_db
            self.db = local_db
            self.db_type = "sqlite"
            logger.info("✅ Используется локальная SQLite база данных")
        except ImportError:
            try:
                # Если локальной нет, пробуем Supabase
                from shared.database import db
                self.db = db
                self.db_type = "supabase"
                logger.info("✅ Используется Supabase база данных")
            except ImportError:
                logger.error("❌ Нет доступной базы данных")
                self.db_type = "none"
    
    def get_database(self):
        """Получить экземпляр базы данных"""
        return self.db
    
    def get_type(self):
        """Получить тип базы данных"""
        return self.db_type

# Глобальный экземпляр
db_manager = DatabaseManager()