from dataclasses import dataclass

from engine.core.broker import SimBroker
from engine.core.event import MarketEvent, OrderEvent
from engine.core.portfolio import Portfolio
from engine.risk.position_sizer import target_qty_from_weight
from engine.risk.risk_manager import (
    apply_max_exposure,
    apply_max_notional,
    apply_turnover_limit,
    clamp_weight,
)


@dataclass
class EngineConfig:
    """Configuration for capital, execution frictions, latency, and risk controls."""

    initial_cash: float = 100_000.0
    fee_bps: float = 1.0
    slippage_bps: float = 2.0
    spread_bps: float = 1.0

    # Phase 3 realism controls
    latency_bars: int = 0
    max_abs_weight: float = 1.0
    max_turnover_qty: float | None = None
    max_notional: float | None = None
    max_abs_exposure: float | None = None


@dataclass
class PendingOrder:
    """Order scheduled for execution once the current bar index reaches `ready_at_index`."""

    order: OrderEvent
    ready_at_index: int


class BacktestEngine:
    """Event-driven backtest engine for single-asset strategies."""

    def __init__(self, config: EngineConfig) -> None:
        """Initialize broker, portfolio state, and pending-order queue."""
        self.config = config
        self.portfolio = Portfolio(initial_cash=config.initial_cash)
        self.broker = SimBroker(
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
            spread_bps=config.spread_bps,
        )
        self.pending_orders: list[PendingOrder] = []

    def _execute_ready_orders(self, bar: MarketEvent, bar_idx: int) -> None:
        """Execute all orders whose readiness time has arrived on the current bar.

        Conditional orders (e.g. LIMIT/STOP) that are not triggered remain pending.
        Filled orders update portfolio cash/position immediately.
        """
        still_pending: list[PendingOrder] = []
        for pending in self.pending_orders:
            if pending.ready_at_index > bar_idx:
                still_pending.append(pending)
                continue

            fill = self.broker.execute(order=pending.order, bar=bar)
            if fill is None:
                # Keep conditional orders alive after their ready time.
                still_pending.append(pending)
                continue

            self.portfolio.on_fill(
                side=fill.side,
                quantity=fill.quantity,
                fill_price=fill.fill_price,
                fee=fill.fee,
            )

        self.pending_orders = still_pending

    def run(self, bars: list[MarketEvent], strategy) -> list[float]:
        """Run the strategy on a bar sequence and return the resulting equity curve.

        Flow per bar:
        1) mark portfolio to market,
        2) execute any ready pending orders,
        3) compute target exposure,
        4) apply configured risk constraints,
        5) schedule a rebalance market order with optional latency.
        """
        latency = max(0, int(self.config.latency_bars))

        for i, bar in enumerate(bars):
            self.portfolio.mark_to_market(price=bar.close)
            self._execute_ready_orders(bar=bar, bar_idx=i)
            self.portfolio.mark_to_market(price=bar.close)

            target_weight = strategy.on_bar(bar)
            target_weight = apply_max_exposure(target_weight, max_abs_exposure=self.config.max_abs_exposure)
            target_weight = clamp_weight(target_weight, max_abs_weight=self.config.max_abs_weight)

            target_qty = target_qty_from_weight(
                equity=self.portfolio.state.equity,
                price=bar.close,
                target_weight=target_weight,
            )
            target_qty = apply_max_notional(
                target_qty=target_qty,
                price=bar.close,
                max_notional=self.config.max_notional,
            )
            target_qty = apply_turnover_limit(
                target_qty=target_qty,
                current_qty=self.portfolio.state.position_qty,
                max_turnover_qty=self.config.max_turnover_qty,
            )

            delta = target_qty - self.portfolio.state.position_qty
            if abs(delta) < 1e-9:
                continue

            side = "BUY" if delta > 0 else "SELL"
            order = OrderEvent(
                timestamp=bar.timestamp,
                symbol=bar.symbol,
                side=side,
                quantity=abs(delta),
                order_type="MARKET",
            )
            self.pending_orders.append(PendingOrder(order=order, ready_at_index=i + latency))

        return self.portfolio.equity_curve
