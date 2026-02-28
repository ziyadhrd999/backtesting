from engine.core.portfolio import Portfolio


def test_portfolio_updates_equity_after_fill_and_mark():
    p = Portfolio(initial_cash=1000)
    p.mark_to_market(10)
    p.on_fill(side="BUY", quantity=10, fill_price=10, fee=1)
    p.mark_to_market(12)
    assert round(p.state.equity, 2) == 1019.0
