from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class MarketEvent:
    timestamp: str
    symbol: str
    close: float
    open: float | None = None
    high: float | None = None
    low: float | None = None
    volume: float | None = None

    def __post_init__(self) -> None:
        # Keep backward compatibility for close-only bars.
        if self.open is None:
            object.__setattr__(self, "open", self.close)
        if self.high is None:
            object.__setattr__(self, "high", self.close)
        if self.low is None:
            object.__setattr__(self, "low", self.close)
        if self.volume is None:
            object.__setattr__(self, "volume", 0.0)


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
    order_type: Literal["MARKET", "LIMIT", "STOP"] = "MARKET"
    limit_price: float | None = None
    stop_price: float | None = None


@dataclass(frozen=True)
class FillEvent:
    timestamp: str
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
    fill_price: float
    fee: float
