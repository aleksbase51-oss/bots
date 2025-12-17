from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass
class Wallet:
    telegram_id: int
    wallet_address: str  # В формате UQ/EQ
    friendly_name: Optional[str] = None
    id: Optional[str] = None  # UUID из Supabase
    created_at: Optional[datetime] = None


@dataclass
class WalletBalance:
    wallet_address: str
    ton_balance: Decimal  # В нанотонах
    spw_balance: Decimal  # В нанотокенах SPW
    ton_human: str  # Человекочитаемый формат TON
    spw_human: str  # Человекочитаемый формат SPW
    last_updated: datetime


@dataclass
class WalletBalanceHistory:
    """История балансов кошелька для статистики"""
    wallet_address: str
    ton_balance: Decimal  # В нанотонах
    spw_balance: Decimal  # В нанотокенах SPW
    recorded_at: datetime  # Когда был записан баланс
    id: Optional[str] = None  # UUID из Supabase
    telegram_id: Optional[int] = None  # Для связи с пользователем