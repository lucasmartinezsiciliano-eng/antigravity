from pydantic import BaseModel, field_validator
from typing import Literal
from datetime import datetime


class Signal(BaseModel):
    action: Literal["BUY", "SELL", "CLOSE"]
    symbol: str                  # "NQ1!", "ES1!", "AAPL", "EURUSD"
    timeframe: str               # "1", "5", "15"
    close: float                 # price at signal time
    time: str                    # ISO timestamp from TradingView
    reason: str                  # "IFVG_long", "IFVG_short"

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        return v.strip().upper()

    @field_validator("action")
    @classmethod
    def normalize_action(cls, v: str) -> str:
        return v.strip().upper()


class TradeLog(BaseModel):
    timestamp: str
    symbol: str
    action: str
    qty: int
    entry_price: float
    stop_loss: float
    take_profit: float
    reason: str
    account_value: float
    risk_usd: float
