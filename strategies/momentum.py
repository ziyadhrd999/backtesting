from collections import deque

from strategies.base_strategy import BaseStrategy


class MomentumStrategy(BaseStrategy):
    def __init__(self, lookback: int = 30) -> None:
        self.lookback = lookback
        self.prices_by_symbol: dict[str, deque[float]] = {}

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        if not bars_by_symbol:
            return {}

        targets: dict[str, float] = {}
        for symbol, market_event in bars_by_symbol.items():
            prices = self.prices_by_symbol.setdefault(symbol, deque(maxlen=self.lookback + 1))
            prices.append(market_event.close)
            if len(prices) < self.lookback + 1:
                targets[symbol] = 0.0
                continue

            ret = (prices[-1] / prices[0]) - 1
            targets[symbol] = 1.0 if ret > 0 else -1.0

        return targets
