from analytics.extended import (
    benchmark_comparison,
    drawdown_duration,
    make_tearsheet_extended,
    rolling_sharpe,
    trade_list_from_fills,
)
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import FillEvent, MarketEvent


class ConstantWeightStrategy:
    def __init__(self, weight: float) -> None:
        self.weight = weight

    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        symbol = next(iter(bars_by_symbol.keys()))
        return {symbol: self.weight}


def _bars(n: int, start: float = 100.0, step: float = 1.0) -> list[MarketEvent]:
    bars = []
    for i in range(n):
        px = start + i * step
        bars.append(MarketEvent(timestamp=f"t{i}", symbol="S", open=px, high=px, low=px, close=px, volume=1000))
    return bars


def test_run_detailed_includes_fill_and_series():
    engine = BacktestEngine(EngineConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0))
    result = engine.run_detailed(_bars(5), ConstantWeightStrategy(1.0))

    assert len(result.equity_curve) > 0
    assert len(result.timestamps) == 5
    assert len(result.positions) == 5
    assert len(result.cash_series) == 5
    assert len(result.fills) >= 1


def test_trade_list_and_extended_tearsheet_metrics():
    fills = [
        FillEvent(timestamp="t0", symbol="S", side="BUY", quantity=10.0, fill_price=100.0, fee=0.0),
        FillEvent(timestamp="t1", symbol="S", side="SELL", quantity=10.0, fill_price=110.0, fee=0.0),
    ]
    trades = trade_list_from_fills(fills)
    assert len(trades) == 1
    assert trades[0]["pnl"] == 100.0

    metrics = make_tearsheet_extended(
        equity_curve=[1000, 1010, 1020, 1030, 1040],
        fills=fills,
        positions=[10, 10, 10, 10, 0],
        prices=[100, 101, 102, 103, 104],
        rolling_window=2,
    )
    assert metrics["NumTrades"] == 1
    assert metrics["WinRate"] == 1.0
    assert "Turnover" in metrics
    assert "MaxDrawdownDurationBars" in metrics


def test_rolling_and_drawdown_and_benchmark_metrics():
    roll = rolling_sharpe([100, 101, 99, 102, 101, 103], window=2)
    assert len(roll) > 0

    dd = drawdown_duration([100, 110, 105, 103, 111, 109])
    assert dd["MaxDrawdownDurationBars"] >= 1

    comp = benchmark_comparison([100, 105, 110], [100, 102, 104], annualization=2)
    assert "InformationRatio" in comp
