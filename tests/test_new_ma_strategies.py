from engine.core.event import MarketEvent
from strategies.hull_moving_average import HullMovingAverageStrategy
from strategies.kama import KAMAStrategy
from strategies.zlema import ZLEMAStrategy


def _run_series(strategy, prices: list[float]) -> float:
    target = 0.0
    for i, price in enumerate(prices):
        bars = {"S": MarketEvent(timestamp=f"t{i}", symbol="S", open=price, high=price, low=price, close=price, volume=100)}
        target = strategy.on_bars(bars)["S"]
    return target


def test_hma_trend_signal_direction() -> None:
    long_target = _run_series(HullMovingAverageStrategy(fast_window=8, slow_window=20), [float(i) for i in range(1, 80)])
    short_target = _run_series(HullMovingAverageStrategy(fast_window=8, slow_window=20), [float(i) for i in range(80, 1, -1)])
    assert long_target == 1.0
    assert short_target == -1.0


def test_kama_price_vs_kama_signal_direction() -> None:
    long_target = _run_series(KAMAStrategy(er_window=10, fast_period=2, slow_period=30), [float(i) for i in range(1, 80)])
    short_target = _run_series(KAMAStrategy(er_window=10, fast_period=2, slow_period=30), [float(i) for i in range(80, 1, -1)])
    assert long_target == 1.0
    assert short_target == -1.0


def test_zlema_cross_signal_direction() -> None:
    long_target = _run_series(ZLEMAStrategy(fast_window=10, slow_window=30), [float(i) for i in range(1, 100)])
    short_target = _run_series(ZLEMAStrategy(fast_window=10, slow_window=30), [float(i) for i in range(100, 1, -1)])
    assert long_target == 1.0
    assert short_target == -1.0
