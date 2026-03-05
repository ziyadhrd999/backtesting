from collections import deque

from strategies.base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    def __init__(self, window: int = 20, z_threshold: float = 1.5) -> None:
        self.window = window
        self.z_threshold = z_threshold
        self.prices_by_symbol: dict[str, deque[float]] = {}

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        if not bars_by_symbol:
            return {}

        targets: dict[str, float] = {}
        for symbol, market_event in bars_by_symbol.items():
            prices = self.prices_by_symbol.setdefault(symbol, deque(maxlen=self.window))
            prices.append(market_event.close)
            if len(prices) < self.window:
                targets[symbol] = 0.0
                continue

            values = list(prices)
            mean = sum(values) / len(values)
            var = sum((x - mean) ** 2 for x in values) / len(values)
            std = var ** 0.5
            if std == 0:
                targets[symbol] = 0.0
                continue

            z = (values[-1] - mean) / std
            if z > self.z_threshold:
                targets[symbol] = -1.0
            elif z < -self.z_threshold:
                targets[symbol] = 1.0
            else:
                targets[symbol] = 0.0

        return targets
