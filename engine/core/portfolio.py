from dataclasses import dataclass


@dataclass
class PortfolioState:
    cash: float
    position_qty: float = 0.0
    last_price: float = 0.0

    @property
    def market_value(self) -> float:
        return self.position_qty * self.last_price

    @property
    def equity(self) -> float:
        return self.cash + self.market_value


class Portfolio:
    def __init__(self, initial_cash: float) -> None:
        self.state = PortfolioState(cash=initial_cash)
        self.equity_curve: list[float] = []

    def on_fill(self, side: str, quantity: float, fill_price: float, fee: float) -> None:
        signed_qty = quantity if side == "BUY" else -quantity
        cash_change = -(signed_qty * fill_price) - fee
        self.state.cash += cash_change
        self.state.position_qty += signed_qty

    def mark_to_market(self, price: float) -> None:
        self.state.last_price = price
        self.equity_curve.append(self.state.equity)
