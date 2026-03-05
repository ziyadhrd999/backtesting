from dataclasses import dataclass, field


@dataclass
class PortfolioState:
    cash: float
    positions: dict[str, float] = field(default_factory=dict)
    last_prices: dict[str, float] = field(default_factory=dict)

    @property
    def position_qty(self) -> float:
        """Compatibility view for legacy single-symbol callers."""
        if len(self.positions) == 1:
            return float(next(iter(self.positions.values())))
        return 0.0

    @property
    def last_price(self) -> float:
        """Compatibility view for legacy single-symbol callers."""
        if len(self.last_prices) == 1:
            return float(next(iter(self.last_prices.values())))
        return 0.0

    @property
    def market_value_by_symbol(self) -> dict[str, float]:
        """Per-symbol marked-to-market notional."""
        return {
            symbol: qty * float(self.last_prices.get(symbol, 0.0))
            for symbol, qty in self.positions.items()
        }

    @property
    def market_value(self) -> float:
        """Total marked-to-market value across all symbols."""
        return sum(self.market_value_by_symbol.values())

    @property
    def equity(self) -> float:
        """Total portfolio equity as cash plus marked position value."""
        return self.cash + self.market_value


class Portfolio:
    def __init__(self, initial_cash: float) -> None:
        self.state = PortfolioState(cash=initial_cash)
        self.equity_curve: list[float] = []

    def on_fill(self, side: str, quantity: float, fill_price: float, fee: float, symbol: str) -> None:
        """Update cash and symbol position after a fill."""
        signed_qty = quantity if side == "BUY" else -quantity
        cash_change = -(signed_qty * fill_price) - fee
        self.state.cash += cash_change
        self.state.positions[symbol] = float(self.state.positions.get(symbol, 0.0) + signed_qty)
        self.state.last_prices[symbol] = float(fill_price)

    def mark_to_market(self, price: float, symbol: str) -> None:
        """Update latest symbol price and append current equity."""
        self.state.last_prices[symbol] = float(price)
        self.equity_curve.append(self.state.equity)
