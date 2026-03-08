from engine.accounting import AccountingLedger
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import FillEvent, MarketEvent


def test_ledger_realized_and_unrealized_pnl_weighted_average_cost() -> None:
    ledger = AccountingLedger(initial_cash=1_000.0)

    ledger.on_fill(FillEvent(timestamp="t0", symbol="S", side="BUY", quantity=10.0, fill_price=100.0, fee=0.0))
    ledger.on_fill(FillEvent(timestamp="t1", symbol="S", side="SELL", quantity=4.0, fill_price=110.0, fee=0.0))
    ledger.on_mark(timestamp="t1", prices_by_symbol={"S": 105.0}, cash=0.0)

    rows = [r for r in ledger.positions_by_symbol if r["symbol"] == "S"]
    assert len(rows) == 1
    row = rows[0]

    assert row["quantity"] == 6.0
    assert row["realized_pnl"] == 40.0
    assert row["unrealized_pnl"] == 30.0


def test_ledger_financing_accrues_on_short_inventory() -> None:
    ledger = AccountingLedger(initial_cash=1_000.0, borrow_rate_bps=100.0, financing_bars_per_year=100)

    ledger.on_fill(FillEvent(timestamp="t0", symbol="S", side="SELL", quantity=10.0, fill_price=100.0, fee=0.0))
    ledger.on_mark(timestamp="t0", prices_by_symbol={"S": 100.0}, cash=2_000.0)

    borrow_entries = [e for e in ledger.journal_entries if e.entry_type == "BORROW_COST"]
    assert len(borrow_entries) == 1
    # notional=1000, rate=1%, dt=1/100 -> cost=0.1
    assert round(abs(borrow_entries[0].amount), 6) == 0.1


def test_engine_run_detailed_includes_accounting_series() -> None:
    bars = [
        MarketEvent(timestamp="t0", symbol="AAPL", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t0", symbol="MSFT", open=100, high=100, low=100, close=100, volume=1000),
        MarketEvent(timestamp="t1", symbol="AAPL", open=110, high=110, low=110, close=110, volume=1000),
        MarketEvent(timestamp="t1", symbol="MSFT", open=90, high=90, low=90, close=90, volume=1000),
    ]

    class EqualWeight:
        def on_bars(self, bars_by_symbol) -> dict[str, float]:
            return {symbol: 0.5 for symbol in bars_by_symbol}

    engine = BacktestEngine(EngineConfig(initial_cash=1_000, fee_bps=0, slippage_bps=0, spread_bps=0))
    result = engine.run_detailed(bars, EqualWeight())

    assert len(result.positions_by_symbol) >= 2
    assert len(result.portfolio_history) == len(result.timestamps)
    assert isinstance(result.journal, list)
