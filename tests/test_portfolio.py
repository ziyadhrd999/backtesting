from engine.core.portfolio import Portfolio


def test_portfolio_updates_equity_after_fill_and_mark():
    p = Portfolio(initial_cash=1000)
    p.mark_to_market(10, symbol="NVDA")
    p.on_fill(side="BUY", quantity=10, fill_price=10, fee=1, symbol="NVDA")
    p.mark_to_market(12, symbol="NVDA")
    assert round(p.state.equity, 2) == 1019.0


def test_portfolio_tracks_per_symbol_positions_and_market_value():
    p = Portfolio(initial_cash=1000)

    p.on_fill(side="BUY", quantity=2, fill_price=100, fee=0, symbol="AAPL")
    p.on_fill(side="BUY", quantity=1, fill_price=200, fee=0, symbol="MSFT")

    p.mark_to_market(110, symbol="AAPL")
    p.mark_to_market(180, symbol="MSFT")

    assert p.state.positions["AAPL"] == 2.0
    assert p.state.positions["MSFT"] == 1.0
    assert p.state.market_value_by_symbol["AAPL"] == 220.0
    assert p.state.market_value_by_symbol["MSFT"] == 180.0
    assert p.state.market_value == 400.0
    assert p.state.equity == 1000.0


def test_single_symbol_compatibility_views():
    p = Portfolio(initial_cash=1000)

    p.mark_to_market(10, symbol="NVDA")
    p.on_fill(side="BUY", quantity=5, fill_price=10, fee=0, symbol="NVDA")

    assert p.state.position_qty == 5.0
    assert p.state.last_price == 10.0
