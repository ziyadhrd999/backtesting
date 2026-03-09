from collections import deque
from math import isqrt

from strategies.base_strategy import BaseStrategy


def _wma(values: list[float], window: int) -> list[float]:
    out: list[float] = []
    if window <= 0:
        return [0.0 for _ in values]
    denom = float(window * (window + 1) // 2)
    weights = list(range(1, window + 1))
    for i in range(len(values)):
        if i + 1 < window:
            out.append(0.0)
            continue
        chunk = values[i + 1 - window : i + 1]
        out.append(sum(v * w for v, w in zip(chunk, weights)) / denom)
    return out


def _hma(values: list[float], window: int) -> list[float]:
    if window <= 1:
        return list(values)

    half = max(1, window // 2)
    root = max(1, isqrt(window))

    wma_half = _wma(values, half)
    wma_full = _wma(values, window)
    raw = [2.0 * a - b for a, b in zip(wma_half, wma_full)]
    return _wma(raw, root)


class HullMovingAverageStrategy(BaseStrategy):
    def __init__(self, fast_window: int = 16, slow_window: int = 64) -> None:
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

            fast = _hma(values, self.fast_window)[-1]
            slow = _hma(values, self.slow_window)[-1]
            targets[symbol] = 1.0 if fast > slow else -1.0

        return targets
