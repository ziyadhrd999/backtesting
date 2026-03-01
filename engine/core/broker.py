from engine.core.event import FillEvent, MarketEvent, OrderEvent
from engine.execution.fill_model import simulate_fill


class SimBroker:
    """Broker simulator that decides if/how an order fills on a given bar.

    Args:
        fee_bps: Fee in basis points applied to traded notional.
        slippage_bps: Slippage in basis points applied by side.
        spread_bps: Half-spread proxy in basis points.

    Example:
        >>> broker = SimBroker(fee_bps=1.0, slippage_bps=2.0, spread_bps=1.0)
        >>> bar = MarketEvent(timestamp="t", symbol="S", open=100, high=101, low=99, close=100)
        >>> order = OrderEvent(timestamp="t", symbol="S", side="BUY", quantity=1)
        >>> fill = broker.execute(order, bar)
        >>> fill is not None
        True
    """

    def __init__(self, fee_bps: float, slippage_bps: float, spread_bps: float = 0.0) -> None:
        """Store execution-friction assumptions used when simulating fills.

        Args:
            fee_bps: Fee in basis points.
            slippage_bps: Slippage in basis points.
            spread_bps: Spread in basis points.

        Example:
            >>> SimBroker(fee_bps=0, slippage_bps=0, spread_bps=0)
            <engine.core.broker.SimBroker object ...>
        """
        self.fee_bps = fee_bps
        self.slippage_bps = slippage_bps
        self.spread_bps = spread_bps

    def execute(self, order: OrderEvent, bar: MarketEvent) -> FillEvent | None:
        """Try to execute an order on a single market bar.

        Args:
            order: Requested order (MARKET/LIMIT/STOP).
            bar: Current OHLCV bar used for trigger/fill checks.

        Returns:
            A :class:`FillEvent` when the order is filled, otherwise ``None``.

        Example:
            >>> broker = SimBroker(fee_bps=0, slippage_bps=0, spread_bps=0)
            >>> bar = MarketEvent(timestamp="t", symbol="S", open=100, high=101, low=99, close=100)
            >>> limit = OrderEvent(timestamp="t", symbol="S", side="BUY", quantity=1, order_type="LIMIT", limit_price=99.5)
            >>> broker.execute(limit, bar) is not None
            True
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
