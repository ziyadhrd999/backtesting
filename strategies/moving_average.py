from collections import deque

from engine.features.indicators import sma
from strategies.base_strategy import BaseStrategy


class MovingAverageStrategy(BaseStrategy):
    def __init__(self, fast_window: int = 20, slow_window: int = 100) -> None:
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.prices_by_symbol: dict[str, deque[float]] = {}

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        if not bars_by_symbol:
            return {}

        targets: dict[str, float] = {}
        for symbol, market_event in bars_by_symbol.items():
            prices = self.prices_by_symbol.setdefault(symbol, deque(maxlen=self.slow_window))
            prices.append(market_event.close)
            values = list(prices)
            if len(values) < self.slow_window:
                targets[symbol] = 0.0
                continue

            fast = sma(values, self.fast_window)[-1]
            slow = sma(values, self.slow_window)[-1]
            targets[symbol] = 1.0 if fast > slow else -1.0

        return targets
