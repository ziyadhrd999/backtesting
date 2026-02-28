from engine.execution.fill_model import simulate_fill


def test_simulate_fill_buy_has_positive_slippage_and_fee():
    fill_price, fee = simulate_fill(price=100, quantity=2, side="BUY", fee_bps=10, slippage_bps=5)
    assert fill_price > 100
    assert fee > 0
