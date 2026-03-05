from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import MarketEvent


class EqualWeightTwoAssetStrategy:
    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        return {symbol: 0.5 for symbol in bars_by_symbol}


class DropSecondAssetStrategy:
    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        timestamp = next(iter(bars_by_symbol.values())).timestamp
        if timestamp == "t0":
            return {"AAPL": 0.5, "MSFT": 0.5}
        return {"AAPL": 0.5}


class OverAllocatedStrategy:
    def on_bars(self, bars_by_symbol) -> dict[str, float]:
        return {symbol: 1.0 for symbol in bars_by_symbol}


def _two_asset_bars() -> list[MarketEvent]:
    return [
        MarketEvent(timestamp="t0", symbol="AAPL", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t0", symbol="MSFT", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t1", symbol="AAPL", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t1", symbol="MSFT", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t2", symbol="AAPL", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t2", symbol="MSFT", open=100, high=100, low=100, close=100, volume=1000),
    ]


def test_engine_rebalances_across_all_symbols_per_timestamp():
    engine = BacktestEngine(EngineConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0))
    engine.run(_two_asset_bars(), EqualWeightTwoAssetStrategy())

    assert engine.portfolio.state.positions["AAPL"] == 5.0
    assert engine.portfolio.state.positions["MSFT"] == 5.0


def test_missing_symbol_target_flattens_position_when_bar_exists():
    engine = BacktestEngine(EngineConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0))
    engine.run(_two_asset_bars(), DropSecondAssetStrategy())

    assert engine.portfolio.state.positions["AAPL"] == 5.0
    assert engine.portfolio.state.positions.get("MSFT", 0.0) == 0.0


def test_cash_only_mode_prevents_negative_cash_on_buys():
    engine = BacktestEngine(EngineConfig(initial_cash=1000, fee_bps=0, slippage_bps=0, spread_bps=0))
    result = engine.run_detailed(_two_asset_bars(), OverAllocatedStrategy())

    assert all(cash >= -1e-9 for cash in result.cash_series)
    assert engine.portfolio.state.cash >= -1e-9
