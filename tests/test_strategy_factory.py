from strategies.factory import build_strategy
from strategies.hull_moving_average import HullMovingAverageStrategy
from strategies.kama import KAMAStrategy
from strategies.moving_average import MovingAverageStrategy
from strategies.zlema import ZLEMAStrategy


def test_factory_builds_moving_average_from_alias() -> None:
    strategy = build_strategy("ma", {"fast_window": 5, "slow_window": 20})
    assert isinstance(strategy, MovingAverageStrategy)
    assert strategy.fast_window == 5
    assert strategy.slow_window == 20


def test_factory_builds_hma_from_alias() -> None:
    strategy = build_strategy("hma", {"fast_window": 12, "slow_window": 48})
    assert isinstance(strategy, HullMovingAverageStrategy)
    assert strategy.fast_window == 12
    assert strategy.slow_window == 48


def test_factory_builds_kama() -> None:
    strategy = build_strategy("kama", {"er_window": 8, "fast_period": 2, "slow_period": 20})
    assert isinstance(strategy, KAMAStrategy)
    assert strategy.er_window == 8
    assert strategy.fast_period == 2
    assert strategy.slow_period == 20


def test_factory_builds_zlema() -> None:
    strategy = build_strategy("zlema", {"fast_window": 10, "slow_window": 40})
    assert isinstance(strategy, ZLEMAStrategy)
    assert strategy.fast_window == 10
    assert strategy.slow_window == 40
