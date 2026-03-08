from __future__ import annotations

from dataclasses import dataclass, field

from engine.core.event import FillEvent


@dataclass
class JournalEntry:
    timestamp: str
    symbol: str
    entry_type: str
    amount: float
    details: str = ""


@dataclass
class SymbolAccountingState:
    quantity: float = 0.0
    avg_cost: float = 0.0
    realized_pnl: float = 0.0
    fees_paid: float = 0.0
    financing_paid: float = 0.0


@dataclass
class PortfolioSnapshot:
    timestamp: str
    cash: float
    equity: float
    gross_exposure: float
    net_exposure: float


class AccountingLedger:
    """Tracks per-symbol accounting and portfolio snapshots.

    The ledger is intentionally independent from execution logic. The engine
    pushes fill and mark events into this class to maintain auditable accounting
    records and symbol-level state histories.
    """

    def __init__(
        self,
        *,
        initial_cash: float,
        borrow_rate_bps: float = 0.0,
        financing_bars_per_year: int = 252,
    ) -> None:
        self.initial_cash = float(initial_cash)
        self.borrow_rate_bps = float(borrow_rate_bps)
        self.financing_bars_per_year = max(1, int(financing_bars_per_year))

        self._states: dict[str, SymbolAccountingState] = {}

        self.journal: list[JournalEntry] = []
        self.symbol_snapshots: list[dict[str, float | str]] = []
        self.portfolio_snapshots: list[PortfolioSnapshot] = []
        self.trade_attribution: list[dict[str, float | str]] = []

    def _state(self, symbol: str) -> SymbolAccountingState:
        return self._states.setdefault(symbol, SymbolAccountingState())

    def on_fill(self, fill: FillEvent) -> None:
        """Apply a fill to cost-basis and realized-PnL accounting.

        Uses weighted-average cost basis and supports direction flips.
        """
        state = self._state(fill.symbol)
        signed_qty = fill.quantity if fill.side == "BUY" else -fill.quantity
        prev_qty = state.quantity

        # Fees are charged immediately and tracked per-symbol.
        state.fees_paid += fill.fee
        self.journal.append(
            JournalEntry(
                timestamp=fill.timestamp,
                symbol=fill.symbol,
                entry_type="FEE",
                amount=-float(fill.fee),
            )
        )

        if abs(prev_qty) < 1e-12 or (prev_qty > 0 and signed_qty > 0) or (prev_qty < 0 and signed_qty < 0):
            # Opening or increasing same direction.
            new_qty = prev_qty + signed_qty
            if abs(new_qty) > 1e-12:
                if abs(prev_qty) < 1e-12:
                    state.avg_cost = float(fill.fill_price)
                else:
                    state.avg_cost = (
                        (abs(prev_qty) * state.avg_cost) + (abs(signed_qty) * float(fill.fill_price))
                    ) / abs(new_qty)
            state.quantity = new_qty
            return

        # Reducing or flipping an existing position.
        closing_qty = min(abs(prev_qty), abs(signed_qty))
        if prev_qty > 0:
            # Closing long with sell.
            realized = (float(fill.fill_price) - state.avg_cost) * closing_qty
        else:
            # Closing short with buy.
            realized = (state.avg_cost - float(fill.fill_price)) * closing_qty

        state.realized_pnl += realized
        self.journal.append(
            JournalEntry(
                timestamp=fill.timestamp,
                symbol=fill.symbol,
                entry_type="REALIZED_PNL",
                amount=float(realized),
            )
        )

        new_qty = prev_qty + signed_qty
        if abs(new_qty) < 1e-12:
            state.quantity = 0.0
            state.avg_cost = 0.0
        elif prev_qty * new_qty > 0:
            # Partial close, same direction remains.
            state.quantity = new_qty
        else:
            # Direction flip: remaining quantity is opened at fill price.
            state.quantity = new_qty
            state.avg_cost = float(fill.fill_price)

        self.trade_attribution.append(
            {
                "timestamp": fill.timestamp,
                "symbol": fill.symbol,
                "closed_qty": float(closing_qty),
                "realized_pnl": float(realized),
                "fill_price": float(fill.fill_price),
                "avg_cost_before": float(state.avg_cost if prev_qty == 0 else state.avg_cost),
            }
        )

    def _accrue_financing(self, timestamp: str, prices_by_symbol: dict[str, float]) -> None:
        if self.borrow_rate_bps <= 0:
            return

        rate = self.borrow_rate_bps / 10_000.0
        dt = 1.0 / self.financing_bars_per_year
        for symbol, state in self._states.items():
            if state.quantity >= -1e-12:
                continue
            price = float(prices_by_symbol.get(symbol, 0.0))
            if price <= 0:
                continue
            notional = abs(state.quantity) * price
            cost = notional * rate * dt
            if cost <= 0:
                continue
            state.financing_paid += cost
            self.journal.append(
                JournalEntry(
                    timestamp=timestamp,
                    symbol=symbol,
                    entry_type="BORROW_COST",
                    amount=-float(cost),
                )
            )

    def on_mark(self, *, timestamp: str, prices_by_symbol: dict[str, float], cash: float) -> None:
        """Record end-of-basket accounting snapshots and optional financing accrual."""
        self._accrue_financing(timestamp=timestamp, prices_by_symbol=prices_by_symbol)

        gross = 0.0
        net = 0.0
        equity = float(cash)

        for symbol, state in self._states.items():
            price = float(prices_by_symbol.get(symbol, 0.0))
            market_value = state.quantity * price
            unrealized = (price - state.avg_cost) * state.quantity if abs(state.quantity) > 1e-12 else 0.0

            gross += abs(market_value)
            net += market_value
            equity += market_value

            self.symbol_snapshots.append(
                {
                    "timestamp": timestamp,
                    "symbol": symbol,
                    "quantity": float(state.quantity),
                    "avg_cost": float(state.avg_cost),
                    "last_price": price,
                    "market_value": float(market_value),
                    "realized_pnl": float(state.realized_pnl),
                    "unrealized_pnl": float(unrealized),
                    "total_pnl": float(state.realized_pnl + unrealized - state.fees_paid - state.financing_paid),
                    "fees_paid": float(state.fees_paid),
                    "financing_paid": float(state.financing_paid),
                }
            )

        self.portfolio_snapshots.append(
            PortfolioSnapshot(
                timestamp=timestamp,
                cash=float(cash),
                equity=float(equity),
                gross_exposure=float(gross),
                net_exposure=float(net),
            )
        )

    @property
    def positions_by_symbol(self) -> list[dict[str, float | str]]:
        return self.symbol_snapshots

    @property
    def portfolio_history(self) -> list[PortfolioSnapshot]:
        return self.portfolio_snapshots

    @property
    def journal_entries(self) -> list[JournalEntry]:
        return self.journal
