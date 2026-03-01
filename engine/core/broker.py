from engine.core.event import FillEvent, MarketEvent, OrderEvent
from engine.execution.fill_model import simulate_fill


class SimBroker:
    """Simple broker simulator that prices and fills MARKET/LIMIT/STOP orders."""

    def __init__(self, fee_bps: float, slippage_bps: float, spread_bps: float = 0.0) -> None:
        """Store fee/slippage/spread assumptions used by the fill model."""
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.spread_bps = spread_bps

    def execute(self, order: OrderEvent, bar: MarketEvent) -> FillEvent | None:
        """Try to execute an order on a single bar.

        - MARKET: fills at bar close.
        - LIMIT: fills at limit price only if touched within bar range.
        - STOP: triggers when crossed and fills at stop price.

        Returns:
            FillEvent when execution occurs, else None.
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
        elif order.order_type == "STOP":
            if order.stop_price is None:
                raise ValueError("STOP order requires stop_price")
            triggered = (order.side == "BUY" and bar.high >= order.stop_price) or (
                order.side == "SELL" and bar.low <= order.stop_price
            )
            if not triggered:
                return None
            # Stop order becomes a marketable order once triggered.
            price = order.stop_price
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
