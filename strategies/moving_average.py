from collections import deque

from engine.features.indicators import sma
from strategies.base_strategy import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    def __init__(self, fast_window: int = 20, slow_window: int = 100) -> None:
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.prices: deque[float] = deque(maxlen=slow_window)

    def on_bar(self, market_event) -> float:
        self.prices.append(market_event.close)
        values = list(self.prices)
        if len(values) < self.slow_window:
            return 0.0
        fast = sma(values, self.fast_window)[-1]
        slow = sma(values, self.slow_window)[-1]
        return 1.0 if fast > slow else -1.0
