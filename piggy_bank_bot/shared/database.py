# shared/database.py
import os
from supabase import create_client
from shared.config import config
import logging

logger = logging.getLogger(__name__)

class Database:
    """Класс для работы с базой данных Supabase"""
    
    _instance = None
    
    def __init__(self):
        if Database._instance is not None:
            raise Exception("Этот класс — синглтон!")
        
        self.client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
        logger.info("✅ Подключение к Supabase установлено")
    
    @classmethod
    def get_instance(cls):
        """Получить экземпляр базы данных (синглтон)"""
        if cls._instance is None:
            cls._instance = Database()
        return cls._instance
    
    def get_client(self):
        """Получить клиент Supabase"""
        return self.client

# Глобальный экземпляр
db = Database.get_instance()