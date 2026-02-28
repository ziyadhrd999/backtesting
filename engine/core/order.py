from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: float
