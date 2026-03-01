from engine.core.broker import SimBroker
from engine.core.event import MarketEvent, OrderEvent
from engine.execution.fill_model import simulate_fill


def test_simulate_fill_buy_has_positive_slippage_and_fee():
    fill_price, fee = simulate_fill(price=100, quantity=2, side="BUY", fee_bps=10, slippage_bps=5)
    assert fill_price > 100
    assert fee > 0


def test_simulate_fill_with_spread_is_worse_than_no_spread_for_buy():
    no_spread, _ = simulate_fill(price=100, quantity=1, side="BUY", fee_bps=0, slippage_bps=0, spread_bps=0)
    with_spread, _ = simulate_fill(price=100, quantity=1, side="BUY", fee_bps=0, slippage_bps=0, spread_bps=10)
    assert with_spread > no_spread


def test_limit_order_fills_only_when_touched():
    broker = SimBroker(fee_bps=0, slippage_bps=0, spread_bps=0)
    bar = MarketEvent(timestamp="t1", symbol="S", open=100, high=102, low=99, close=101)

    buy_limit_fill = broker.execute(
        order=OrderEvent(timestamp="t1", symbol="S", side="BUY", quantity=1, order_type="LIMIT", limit_price=100),
        bar=bar,
    )
    assert buy_limit_fill is not None
    assert buy_limit_fill.fill_price == 100

    sell_limit_no_fill = broker.execute(
        order=OrderEvent(timestamp="t1", symbol="S", side="SELL", quantity=1, order_type="LIMIT", limit_price=105),
        bar=bar,
    )
    assert sell_limit_no_fill is None


def test_stop_order_fills_only_when_triggered():
    broker = SimBroker(fee_bps=0, slippage_bps=0, spread_bps=0)
    bar = MarketEvent(timestamp="t1", symbol="S", open=100, high=102, low=99, close=101)

    buy_stop_fill = broker.execute(
        order=OrderEvent(timestamp="t1", symbol="S", side="BUY", quantity=1, order_type="STOP", stop_price=101.5),
        bar=bar,
    )
    assert buy_stop_fill is not None
    assert buy_stop_fill.fill_price == 101.5

    sell_stop_no_fill = broker.execute(
        order=OrderEvent(timestamp="t1", symbol="S", side="SELL", quantity=1, order_type="STOP", stop_price=98.5),
        bar=bar,
    )
    assert sell_stop_no_fill is None
