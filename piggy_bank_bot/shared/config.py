# shared/config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    TON_API_KEY = os.getenv("TON_API_KEY")
    
    @classmethod
    def validate(cls):
        required = {
            "BOT_TOKEN": cls.BOT_TOKEN,
            "SUPABASE_URL": cls.SUPABASE_URL,
            "SUPABASE_KEY": cls.SUPABASE_KEY,
            "TON_API_KEY": cls.TON_API_KEY
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Отсутствуют: {', '.join(missing)}")
        return True

config = Config()