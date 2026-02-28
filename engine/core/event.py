from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MarketEvent:
    timestamp: str
    symbol: str
    close: float


@dataclass(frozen=True)
class SignalEvent:
    timestamp: str
    symbol: str
    target_position: float  # -1.0 to +1.0


@dataclass(frozen=True)
class OrderEvent:
    timestamp: str
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float


@dataclass(frozen=True)
class FillEvent:
    timestamp: str
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    fill_price: float
    fee: float
