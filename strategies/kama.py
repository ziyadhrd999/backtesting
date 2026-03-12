from collections import deque

from strategies.base_strategy import BaseStrategy


def _kama(values: list[float], er_window: int, fast_period: int, slow_period: int) -> list[float]:
    if not values:
        return []

    er_window = max(1, er_window)
    fast_sc = 2.0 / (max(1, fast_period) + 1.0)
    slow_sc = 2.0 / (max(1, slow_period) + 1.0)

    out: list[float] = [values[0]]
    for i in range(1, len(values)):
        if i < er_window:
            out.append(values[i])
            continue

        change = abs(values[i] - values[i - er_window])
        volatility = sum(abs(values[j] - values[j - 1]) for j in range(i - er_window + 1, i + 1))
        er = (change / volatility) if volatility > 0 else 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2

        prev = out[-1]
        out.append(prev + sc * (values[i] - prev))

    return out


class KAMAStrategy(BaseStrategy):
    def __init__(self, er_window: int = 10, fast_period: int = 2, slow_period: int = 30) -> None:
        self.er_window = er_window
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices_by_symbol: dict[str, deque[float]] = {}

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        if not bars_by_symbol:
            return {}

        targets: dict[str, float] = {}
        history_len = max(self.er_window * 3, self.slow_period * 3)

        for symbol, market_event in bars_by_symbol.items():
            prices = self.prices_by_symbol.setdefault(symbol, deque(maxlen=history_len))
            prices.append(market_event.close)
            values = list(prices)
            if len(values) < self.er_window + 1:
                targets[symbol] = 0.0
                continue

            kama_value = _kama(values, self.er_window, self.fast_period, self.slow_period)[-1]
            targets[symbol] = 1.0 if values[-1] > kama_value else -1.0

        return targets
