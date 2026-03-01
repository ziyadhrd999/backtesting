from dataclasses import dataclass

from engine.core.broker import SimBroker
from engine.core.event import FillEvent, MarketEvent, OrderEvent
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
    """Runtime configuration for engine behavior and constraints.

    Args:
        initial_cash: Starting account cash.
        fee_bps: Transaction fee in basis points.
        slippage_bps: Slippage in basis points.
        spread_bps: Spread adjustment in basis points.
        latency_bars: Number of bars to wait before a new order becomes executable.
        max_abs_weight: Hard cap on absolute strategy weight.
        max_turnover_qty: Max quantity change allowed per bar.
        max_notional: Max absolute notional exposure per asset.
        max_abs_exposure: Additional cap on absolute strategy exposure.

    Example:
        >>> cfg = EngineConfig(initial_cash=50_000, latency_bars=1, max_notional=10_000)
        >>> (cfg.initial_cash, cfg.latency_bars, cfg.max_notional)
        (50000, 1, 10000)
    """

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
    """Represents an order waiting for latency/trigger conditions.

    Args:
        order: The order payload to execute later.
        ready_at_index: Earliest bar index where execution can be attempted.

    Example:
        >>> order = OrderEvent(timestamp="t0", symbol="S", side="BUY", quantity=1)
        >>> PendingOrder(order=order, ready_at_index=2).ready_at_index
        2
    """

    order: OrderEvent
    ready_at_index: int


@dataclass
class RunResult:
    """Structured output produced by :meth:`BacktestEngine.run_detailed`.

    Attributes:
        equity_curve: Equity value per mark-to-market event.
        fills: Executed fills in chronological order.
        positions: Position quantity per bar.
        cash_series: Cash balance per bar.
        timestamps: Bar timestamps aligned with ``positions``/``cash_series``.

    Example:
        >>> result = RunResult(equity_curve=[1000.0], fills=[], positions=[0.0], cash_series=[1000.0], timestamps=['t0'])
        >>> result.cash_series[-1]
        1000.0
    """

    equity_curve: list[float]
    fills: list[FillEvent]
    positions: list[float]
    cash_series: list[float]
    timestamps: list[str]


class BacktestEngine:
    """Event-driven single-asset backtesting engine.

    Args:
        config: Engine configuration controlling execution and risk behavior.

    Example:
        >>> engine = BacktestEngine(EngineConfig(initial_cash=10_000))
        >>> isinstance(engine.pending_orders, list)
        True
    """

    def __init__(self, config: EngineConfig) -> None:
        """Initialize portfolio, broker, and pending-order state.

        Args:
            config: :class:`EngineConfig` instance with all runtime settings.

        Example:
            >>> engine = BacktestEngine(EngineConfig())
            >>> engine.config.initial_cash
            100000.0
        """
        self.config = config
        self.portfolio = Portfolio(initial_cash=config.initial_cash)
        self.broker = SimBroker(
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
            spread_bps=config.spread_bps,
        )
        self.pending_orders: list[PendingOrder] = []
        self.fill_events: list[FillEvent] = []
        self.position_series: list[float] = []
        self.cash_series: list[float] = []
        self.timestamp_series: list[str] = []

    def _execute_ready_orders(self, bar: MarketEvent, bar_idx: int) -> None:
        """Execute queued orders whose readiness index has been reached.

        Args:
            bar: Current market bar used for trigger and fill checks.
            bar_idx: Integer index of the current bar in the run loop.

        Example:
            >>> # Called internally from `run` on each bar
            >>> # and updates `self.pending_orders` in place.
            >>> pass
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
            self.fill_events.append(fill)

        self.pending_orders = still_pending

    def run(self, bars: list[MarketEvent], strategy) -> list[float]:
        """Run strategy over historical bars and return equity curve.

        Args:
            bars: Ordered sequence of :class:`MarketEvent` bars.
            strategy: Strategy object exposing ``on_bar(bar) -> target_weight``.

        Returns:
            List of equity points produced by the portfolio over time.

        Example:
            >>> class BuyAndHold:
            ...     def on_bar(self, market_event):
            ...         return 1.0
            >>> bars = [MarketEvent(timestamp="t0", symbol="S", close=100.0)]
            >>> curve = BacktestEngine(EngineConfig()).run(bars, BuyAndHold())
            >>> isinstance(curve, list)
            True
        """
        result = self.run_detailed(bars, strategy)
        return result.equity_curve

    def run_detailed(self, bars: list[MarketEvent], strategy) -> RunResult:
        """Run strategy and return rich run artifacts for analytics.

        Args:
            bars: Ordered sequence of market bars.
            strategy: Strategy object exposing ``on_bar(bar) -> target_weight``.

        Returns:
            :class:`RunResult` with equity, fills, and bar-level state series.
        """
        latency = max(0, int(self.config.latency_bars))

        self.portfolio = Portfolio(initial_cash=self.config.initial_cash)
        self.pending_orders = []
        self.fill_events = []
        self.position_series = []
        self.cash_series = []
        self.timestamp_series = []

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
                self.position_series.append(self.portfolio.state.position_qty)
                self.cash_series.append(self.portfolio.state.cash)
                self.timestamp_series.append(bar.timestamp)
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
            self.position_series.append(self.portfolio.state.position_qty)
            self.cash_series.append(self.portfolio.state.cash)
            self.timestamp_series.append(bar.timestamp)

        return RunResult(
            equity_curve=list(self.portfolio.equity_curve),
            fills=list(self.fill_events),
            positions=list(self.position_series),
            cash_series=list(self.cash_series),
            timestamps=list(self.timestamp_series),
        )
