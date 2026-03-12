from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import MarketEvent


class ConstantWeightStrategy:
    def __init__(self, weight: float) -> None:
        self.weight = weight

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        symbol = next(iter(bars_by_symbol.keys()))
        return {symbol: self.weight}


class AlwaysLongStrategy:
    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        symbol = next(iter(bars_by_symbol.keys()))
        return {symbol: 1.0}


class FlipByTimestampStrategy:
    def __init__(self, weights_by_timestamp: dict[str, float]) -> None:
        self.weights_by_timestamp = weights_by_timestamp

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        symbol = next(iter(bars_by_symbol.keys()))
        ts = bars_by_symbol[symbol].timestamp
        return {symbol: self.weights_by_timestamp.get(ts, 0.0)}


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


def test_stop_loss_pct_liquidates_and_reenters_after_cooldown():
    bars = [
        MarketEvent(timestamp="t0", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t1", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t2", symbol="S", open=90, high=90, low=90, close=90, volume=1000),
        MarketEvent(timestamp="t3", symbol="S", open=90, high=90, low=90, close=90, volume=1000),
        MarketEvent(timestamp="t4", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t5", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
    ]

    engine = BacktestEngine(
        EngineConfig(
            initial_cash=1000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            stop_loss_mode="pct",
            stop_loss_value=0.05,
            stop_cooldown_bars=2,
        )
    )
    engine.run_detailed(bars, AlwaysLongStrategy())

    assert engine.portfolio.state.position_qty == 9.0
    sell_fills = [fill for fill in engine.fill_events if fill.side == "SELL"]
    buy_fills = [fill for fill in engine.fill_events if fill.side == "BUY"]
    assert len(sell_fills) >= 1
    assert buy_fills[-1].timestamp == "t4"


def test_stop_loss_notional_liquidates_when_loss_dollars_exceeded():
    bars = [
        MarketEvent(timestamp="t0", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t1", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t2", symbol="S", open=94, high=94, low=94, close=94, volume=1000),
        MarketEvent(timestamp="t3", symbol="S", open=94, high=94, low=94, close=94, volume=1000),
    ]

    engine = BacktestEngine(
        EngineConfig(
            initial_cash=1000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            stop_loss_mode="notional",
            stop_loss_value=50.0,
            stop_cooldown_bars=10,
        )
    )
    engine.run_detailed(bars, AlwaysLongStrategy())

    assert engine.portfolio.state.position_qty == 0.0
    assert any(fill.side == "SELL" for fill in engine.fill_events)


def test_daily_trade_cap_limits_buy_fills_only_and_resets_next_day():
    bars = [
        MarketEvent(timestamp="2024-01-01 09:30", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="2024-01-01 10:00", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="2024-01-01 10:30", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="2024-01-02 09:30", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
    ]
    strategy = FlipByTimestampStrategy(
        {
            "2024-01-01 09:30": 1.0,
            "2024-01-01 10:00": 0.0,
            "2024-01-01 10:30": 1.0,
            "2024-01-02 09:30": 1.0,
        }
    )

    engine = BacktestEngine(
        EngineConfig(
            initial_cash=1000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            max_trades_per_day=1,
            trade_cap_side="buy",
        )
    )
    engine.run_detailed(bars, strategy)

    buy_fills = [fill for fill in engine.fill_events if fill.side == "BUY"]
    sell_fills = [fill for fill in engine.fill_events if fill.side == "SELL"]

    assert [fill.timestamp for fill in buy_fills] == ["2024-01-01 09:30", "2024-01-01 10:30"]
    assert [fill.timestamp for fill in sell_fills] == ["2024-01-01 10:00"]


def test_forced_stop_loss_exit_bypasses_daily_sell_cap():
    bars = [
        MarketEvent(timestamp="2024-01-01 09:00", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="2024-01-01 09:30", symbol="S", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="2024-01-01 10:00", symbol="S", open=90, high=90, low=90, close=90, volume=1000),
        MarketEvent(timestamp="2024-01-01 10:30", symbol="S", open=90, high=90, low=90, close=90, volume=1000),
    ]

    engine = BacktestEngine(
        EngineConfig(
            initial_cash=1000,
            fee_bps=0,
            slippage_bps=0,
            spread_bps=0,
            max_trades_per_day=1,
            trade_cap_side="both",
            stop_loss_mode="pct",
            stop_loss_value=0.05,
            stop_cooldown_bars=10,
        )
    )
    engine.run_detailed(bars, AlwaysLongStrategy())

    buy_fills = [fill for fill in engine.fill_events if fill.side == "BUY"]
    sell_fills = [fill for fill in engine.fill_events if fill.side == "SELL"]
    assert len(buy_fills) == 1
    assert len(sell_fills) >= 1
