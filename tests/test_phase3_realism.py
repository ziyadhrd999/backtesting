from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import MarketEvent


class ConstantWeightStrategy:
    def __init__(self, weight: float) -> None:
        self.weight = weight

    def on_bar(self, market_event) -> float:
        return self.weight


def _bars(n: int, price: float = 100.0) -> list[MarketEvent]:
    return [
        MarketEvent(timestamp=f"t{i}", symbol="S", open=price, high=price, low=price, close=price, volume=1000)
        for i in range(n)
    ]


def test_latency_sets_order_readiness_offset():
    bars = _bars(1, price=100.0)

    immediate = BacktestEngine(EngineConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0, latency_bars=0))
    delayed = BacktestEngine(EngineConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0, latency_bars=1))

    strategy = ConstantWeightStrategy(1.0)
    immediate.run(bars, strategy)
    delayed.run(bars, strategy)

    assert len(immediate.pending_orders) == 1
    assert len(delayed.pending_orders) == 1
    assert immediate.pending_orders[0].ready_at_index == 0
    assert delayed.pending_orders[0].ready_at_index == 1


def test_max_turnover_qty_limits_position_change_per_bar():
    bars = _bars(5, price=100.0)
    engine = BacktestEngine(
        EngineConfig(
            initial_cash=1000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            max_turnover_qty=2.0,
        )
    )
    engine.run(bars, ConstantWeightStrategy(1.0))

    # Without turnover cap, target would be 10 shares quickly; with cap it should climb 2 shares/bar.
    assert engine.portfolio.state.position_qty == 8.0


def test_max_notional_caps_target_position_size():
    bars = _bars(2, price=100.0)
    engine = BacktestEngine(
        EngineConfig(
            initial_cash=10_000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            max_notional=500.0,
        )
    )
    engine.run(bars, ConstantWeightStrategy(1.0))

    assert engine.portfolio.state.position_qty == 5.0


def test_max_abs_exposure_clamps_signal_before_sizing():
    bars = _bars(2, price=100.0)
    engine = BacktestEngine(
        EngineConfig(
            initial_cash=10_000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            max_abs_weight=1.0,
            max_abs_exposure=0.2,
        )
    )
    engine.run(bars, ConstantWeightStrategy(1.0))

    # 20% of 10,000 at 100 price -> 20 shares target.
    assert engine.portfolio.state.position_qty == 20.0
