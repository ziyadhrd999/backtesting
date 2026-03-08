from dataclasses import dataclass
from itertools import groupby

from engine.accounting import AccountingLedger
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
        max_drawdown_pct: Maximum allowed drawdown as a decimal fraction.
            When current drawdown falls below ``-max_drawdown_pct``, the engine
            liquidates long positions and blocks new risk for the remainder of
            the run.
        allow_short: Whether negative target weights and net short positions are allowed.
            Defaults to ``False`` for long-only behavior.

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
    max_drawdown_pct: float | None = None
    allow_short: bool = False
    borrow_rate_bps: float = 0.0
    financing_bars_per_year: int = 252


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
    positions_by_symbol: list[dict[str, float | str]]
    portfolio_history: list[dict[str, float | str]]
    journal: list[dict[str, float | str]]
    trade_attribution: list[dict[str, float | str]]


class BacktestEngine:
    """Event-driven multi-asset backtesting engine.

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
        self.ledger = AccountingLedger(initial_cash=config.initial_cash, borrow_rate_bps=config.borrow_rate_bps, financing_bars_per_year=config.financing_bars_per_year)

    def _execute_ready_orders(self, bars_by_symbol: dict[str, MarketEvent], bar_idx: int) -> None:
        """Execute queued orders whose readiness index has been reached.

        Args:
            bars_by_symbol: Current timestamp bars keyed by symbol.
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

            bar = bars_by_symbol.get(pending.order.symbol)
            if bar is None:
                still_pending.append(pending)
                continue

            order_to_execute = pending.order

            if order_to_execute.side == "SELL" and not self.config.allow_short:
                current_qty = float(self.portfolio.state.positions.get(order_to_execute.symbol, 0.0))
                if current_qty <= 1e-12:
                    continue

                if order_to_execute.quantity > current_qty:
                    order_to_execute = OrderEvent(
                        timestamp=order_to_execute.timestamp,
                        symbol=order_to_execute.symbol,
                        side=order_to_execute.side,
                        quantity=current_qty,
                        order_type=order_to_execute.order_type,
                        limit_price=order_to_execute.limit_price,
                        stop_price=order_to_execute.stop_price,
                    )

            if order_to_execute.side == "BUY":
                fill_preview = self.broker.execute(order=order_to_execute, bar=bar)
                if fill_preview is None:
                    still_pending.append(pending)
                    continue

                required_cash = (fill_preview.quantity * fill_preview.fill_price) + fill_preview.fee
                available_cash = self.portfolio.state.cash
                if required_cash > available_cash:
                    cost_per_unit = fill_preview.fill_price + (fill_preview.fee / fill_preview.quantity)
                    if cost_per_unit <= 0:
                        still_pending.append(pending)
                        continue

                    affordable_qty = available_cash / cost_per_unit
                    if affordable_qty <= 1e-12:
                        still_pending.append(pending)
                        continue

                    order_to_execute = OrderEvent(
                        timestamp=order_to_execute.timestamp,
                        symbol=order_to_execute.symbol,
                        side=order_to_execute.side,
                        quantity=min(order_to_execute.quantity, affordable_qty),
                        order_type=order_to_execute.order_type,
                        limit_price=order_to_execute.limit_price,
                        stop_price=order_to_execute.stop_price,
                    )

            fill = self.broker.execute(order=order_to_execute, bar=bar)
            if fill is None:
                # Keep conditional orders alive after their ready time.
                still_pending.append(pending)
                continue

            self.portfolio.on_fill(
                side=fill.side,
                quantity=fill.quantity,
                fill_price=fill.fill_price,
                fee=fill.fee,
                symbol=fill.symbol,
            )
            self.ledger.on_fill(fill)
            self.fill_events.append(fill)

        self.pending_orders = still_pending

    def _timestamp_baskets(self, bars: list[MarketEvent]) -> list[tuple[str, dict[str, MarketEvent]]]:
        """Group bars into timestamp snapshots keyed by symbol."""
        baskets: list[tuple[str, dict[str, MarketEvent]]] = []
        for timestamp, group in groupby(bars, key=lambda bar: bar.timestamp):
            baskets.append((timestamp, {bar.symbol: bar for bar in group}))
        return baskets

    def run(self, bars: list[MarketEvent], strategy) -> list[float]:
        """Run strategy over historical bars and return equity curve.

        Args:
            bars: Ordered sequence of :class:`MarketEvent` bars.
            strategy: Strategy object exposing
                ``on_bars({symbol: bar, ...}) -> {symbol: target_weight}``.

        Returns:
            List of equity points produced by the portfolio over time.

        Example:
            >>> class BuyAndHold:
            ...     def on_bars(self, bars_by_symbol):
            ...         return {symbol: 1.0 for symbol in bars_by_symbol}
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
            strategy: Strategy object exposing
                ``on_bars({symbol: bar, ...}) -> {symbol: target_weight}``.

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
        self.ledger = AccountingLedger(
            initial_cash=self.config.initial_cash,
            borrow_rate_bps=self.config.borrow_rate_bps,
            financing_bars_per_year=self.config.financing_bars_per_year,
        )

        timestamp_baskets = self._timestamp_baskets(bars)
        peak_equity = self.portfolio.state.equity
        drawdown_liquidation_triggered = False

        for i, (timestamp, bars_by_symbol) in enumerate(timestamp_baskets):
            for symbol, bar in bars_by_symbol.items():
                self.portfolio.mark_to_market(price=bar.close, symbol=symbol)

            if self.portfolio.state.equity > peak_equity:
                peak_equity = self.portfolio.state.equity

            max_drawdown_pct = self.config.max_drawdown_pct
            if (
                max_drawdown_pct is not None
                and max_drawdown_pct > 0
                and peak_equity > 0
                and not drawdown_liquidation_triggered
            ):
                current_drawdown = (self.portfolio.state.equity / peak_equity) - 1.0
                drawdown_liquidation_triggered = current_drawdown <= -max_drawdown_pct

            if drawdown_liquidation_triggered:
                self.pending_orders = [pending for pending in self.pending_orders if pending.order.side == "SELL"]

            self._execute_ready_orders(bars_by_symbol=bars_by_symbol, bar_idx=i)

            for symbol, bar in bars_by_symbol.items():
                self.portfolio.mark_to_market(price=bar.close, symbol=symbol)

            target_weights = {} if drawdown_liquidation_triggered else strategy.on_bars(bars_by_symbol)
            symbols_to_rebalance = set(bars_by_symbol.keys()) | set(self.portfolio.state.positions.keys())

            rebalance_orders: list[OrderEvent] = []
            for symbol in symbols_to_rebalance:
                bar = bars_by_symbol.get(symbol)
                if bar is None:
                    continue

                target_weight = float(target_weights.get(symbol, 0.0))
                target_weight = apply_max_exposure(target_weight, max_abs_exposure=self.config.max_abs_exposure)
                target_weight = clamp_weight(target_weight, max_abs_weight=self.config.max_abs_weight)
                if not self.config.allow_short:
                    target_weight = max(0.0, target_weight)

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
                current_qty = float(self.portfolio.state.positions.get(symbol, 0.0))
                target_qty = apply_turnover_limit(
                    target_qty=target_qty,
                    current_qty=current_qty,
                    max_turnover_qty=self.config.max_turnover_qty,
                )

                delta = target_qty - current_qty
                if abs(delta) < 1e-9:
                    continue

                rebalance_orders.append(
                    OrderEvent(
                        timestamp=timestamp,
                        symbol=symbol,
                        side="BUY" if delta > 0 else "SELL",
                        quantity=abs(delta),
                        order_type="MARKET",
                    )
                )

            sells = [order for order in rebalance_orders if order.side == "SELL"]
            buys = [order for order in rebalance_orders if order.side == "BUY"]
            for order in sells + buys:
                self.pending_orders.append(PendingOrder(order=order, ready_at_index=i + latency))

            self.position_series.append(sum(float(qty) for qty in self.portfolio.state.positions.values()))
            self.cash_series.append(self.portfolio.state.cash)
            self.timestamp_series.append(timestamp)

            self.ledger.on_mark(
                timestamp=timestamp,
                prices_by_symbol={symbol: bar.close for symbol, bar in bars_by_symbol.items()},
                cash=self.portfolio.state.cash,
            )

        return RunResult(
            equity_curve=list(self.portfolio.equity_curve),
            fills=list(self.fill_events),
            positions=list(self.position_series),
            cash_series=list(self.cash_series),
            timestamps=list(self.timestamp_series),
            positions_by_symbol=list(self.ledger.positions_by_symbol),
            portfolio_history=[
                {
                    "timestamp": snap.timestamp,
                    "cash": snap.cash,
                    "equity": snap.equity,
                    "gross_exposure": snap.gross_exposure,
                    "net_exposure": snap.net_exposure,
                }
                for snap in self.ledger.portfolio_history
            ],
            journal=[
                {
                    "timestamp": entry.timestamp,
                    "symbol": entry.symbol,
                    "entry_type": entry.entry_type,
                    "amount": entry.amount,
                    "details": entry.details,
                }
                for entry in self.ledger.journal_entries
            ],
            trade_attribution=list(self.ledger.trade_attribution),
        )
