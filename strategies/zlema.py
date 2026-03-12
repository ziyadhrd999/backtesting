from collections import deque

from strategies.base_strategy import BaseStrategy


def _ema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    period = max(1, period)
    alpha = 2.0 / (period + 1.0)
    out: list[float] = [values[0]]
    for v in values[1:]:
        out.append(alpha * v + (1.0 - alpha) * out[-1])
    return out


def _zlema(values: list[float], period: int) -> list[float]:
    if not values:
        return []
    period = max(1, period)
    lag = max(0, (period - 1) // 2)

    de_lagged: list[float] = []
    for i, price in enumerate(values):
        lagged = values[i - lag] if i >= lag else values[0]
        de_lagged.append(price + (price - lagged))
    return _ema(de_lagged, period)


class ZLEMAStrategy(BaseStrategy):
    def __init__(self, fast_window: int = 20, slow_window: int = 60) -> None:
        self.fast_window = fast_window
        self.slow_window = slow_window
        self.prices_by_symbol: dict[str, deque[float]] = {}

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        if not bars_by_symbol:
            return {}

        targets: dict[str, float] = {}
        history_len = max(self.fast_window, self.slow_window) * 3

        for symbol, market_event in bars_by_symbol.items():
            prices = self.prices_by_symbol.setdefault(symbol, deque(maxlen=history_len))
            prices.append(market_event.close)
            values = list(prices)
            if len(values) < max(self.fast_window, self.slow_window):
                targets[symbol] = 0.0
                continue

            fast = _zlema(values, self.fast_window)[-1]
            slow = _zlema(values, self.slow_window)[-1]
            targets[symbol] = 1.0 if fast > slow else -1.0

        return targets
