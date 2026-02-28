from engine.core.event import FillEvent, OrderEvent
from engine.execution.fill_model import simulate_fill


class SimBroker:
    def __init__(self, fee_bps: float, slippage_bps: float) -> None:
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps

    def execute(self, order: OrderEvent, market_price: float) -> FillEvent:
        fill_price, fee = simulate_fill(
            price=market_price,
            quantity=order.quantity,
            side=order.side,
            fee_bps=self.fee_bps,
            slippage_bps=self.slippage_bps,
        )
        return FillEvent(
            timestamp=order.timestamp,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            fee=fee,
        )
