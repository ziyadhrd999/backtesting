from strategies.factory import build_strategy
from strategies.moving_average import MovingAverageStrategy


def test_factory_builds_moving_average_from_alias() -> None:
    strategy = build_strategy("ma", {"fast_window": 5, "slow_window": 20})
    assert isinstance(strategy, MovingAverageStrategy)
    assert strategy.fast_window == 5
    assert strategy.slow_window == 20
