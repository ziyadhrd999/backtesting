from collections import deque

from strategies.base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    def __init__(self, window: int = 20, z_threshold: float = 1.5) -> None:
        self.window = window
        self.z_threshold = z_threshold
        self.prices: deque[float] = deque(maxlen=window)

    def on_bar(self, market_event) -> float:
        self.prices.append(market_event.close)
        if len(self.prices) < self.window:
            return 0.0
        values = list(self.prices)
        mean = sum(values) / len(values)
        var = sum((x - mean) ** 2 for x in values) / len(values)
        std = var ** 0.5
        if std == 0:
            return 0.0
        z = (values[-1] - mean) / std
        if z > self.z_threshold:
            return -1.0
        if z < -self.z_threshold:
            return 1.0
        return 0.0
