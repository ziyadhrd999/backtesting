from collections import deque

from strategies.base_strategy import BaseStrategy


class MomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 30) -> None:
        self.lookback = lookback
        self.prices: deque[float] = deque(maxlen=lookback + 1)

    def on_bar(self, market_event) -> float:
        self.prices.append(market_event.close)
        if len(self.prices) < self.lookback + 1:
            return 0.0
        ret = (self.prices[-1] / self.prices[0]) - 1
        return 1.0 if ret > 0 else -1.0
