# shared/local_database.py
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class LocalDatabase:
    """Класс для работы с локальной базой данных SQLite"""
    
    _instance = None
    
    def __init__(self, db_path="database.db"):
        if LocalDatabase._instance is not None:
            raise Exception("Этот класс — синглтон!")
        
        self.db_path = db_path
        self.init_database()
        logger.info(f"✅ Локальная база данных SQLite инициализирована: {db_path}")
    
    @classmethod
    def get_instance(cls, db_path="database.db"):
        """Получить экземпляр базы данных (синглтон)"""
        if cls._instance is None:
            cls._instance = LocalDatabase(db_path)
        return cls._instance
    
    def get_connection(self):
        """Получить соединение с базой данных"""
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Инициализировать базу данных и создать таблицы если их нет"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id TEXT UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    spw_balance INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица прогресса уроков
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_lessons (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    lesson_id INTEGER NOT NULL,
                    quiz_score INTEGER NOT NULL,
                    reward_granted BOOLEAN DEFAULT TRUE,
                    completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    UNIQUE(user_id, lesson_id)
                )
            ''')
            
            # Индексы для быстрого поиска
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_lessons_user_id ON user_lessons(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_lessons_lesson_id ON user_lessons(lesson_id)')
            
            conn.commit()
    
    def execute_query(self, query, params=()):
        """Выполнить SQL запрос"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
    
    def fetch_one(self, query, params=()):
        """Выполнить запрос и получить одну запись"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetch_all(self, query, params=()):
        """Выполнить запрос и получить все записи"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.fetchall()

# Глобальный экземпляр
local_db = LocalDatabase.get_instance()