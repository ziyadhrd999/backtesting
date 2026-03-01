from engine.core.event import FillEvent, MarketEvent, OrderEvent
from engine.execution.fill_model import simulate_fill


class SimBroker:
    def __init__(self, fee_bps: float, slippage_bps: float, spread_bps: float = 0.0) -> None:
        """
        Initializes the simulated broker with transaction fee, spread, and slippage parameters.
        """
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.spread_bps = spread_bps

    def execute(self, order: OrderEvent, bar: MarketEvent) -> FillEvent | None:
        """
        Execute MARKET orders immediately on close and LIMIT orders when touched within bar range.
        """
        price: float | None
        if order.order_type == "MARKET":
            price = bar.close
        elif order.order_type == "LIMIT":
            if order.limit_price is None:
                raise ValueError("LIMIT order requires limit_price")
            touched = (order.side == "BUY" and bar.low <= order.limit_price) or (
                order.side == "SELL" and bar.high >= order.limit_price
            )
            if not touched:
                return None
            price = order.limit_price
        else:
            raise ValueError(f"Unsupported order_type: {order.order_type}")

        fill_price, fee = simulate_fill(
            price=price,
            quantity=order.quantity,
            side=order.side,
            fee_bps=self.fee_bps,
            slippage_bps=self.slippage_bps,
            spread_bps=self.spread_bps,
        )
        return FillEvent(
            timestamp=order.timestamp,
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            fill_price=fill_price,
            fee=fee,
        )
