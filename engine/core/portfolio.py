from dataclasses import dataclass


@dataclass
class PortfolioState:
    cash: float
    position_qty: float = 0.0
    last_price: float = 0.0

    @property
    def market_value(self) -> float:
        """
        Updates the latest market price and records the portfolio's current equity in the equity curve.
        """
        return self.position_qty * self.last_price

    @property
    def equity(self) -> float:
        """
        → Computes total portfolio value as cash + the market value of the position.
        """
        return self.cash + self.market_value


class Portfolio:
    def __init__(self, initial_cash: float) -> None:
        self.state = PortfolioState(cash=initial_cash)
        self.equity_curve: list[float] = []

    def on_fill(self, side: str, quantity: float, fill_price: float, fee: float) -> None:
        """
        Updates portfolio cash and position after a trade execution.

        Args:
            side: Trade direction ("BUY" or "SELL").
            quantity: Number of units traded.
            fill_price: Execution price of the trade.
            fee: Transaction cost applied to the trade.
        """
        signed_qty = quantity if side == "BUY" else -quantity
        cash_change = -(signed_qty * fill_price) - fee
        self.state.cash += cash_change
        self.state.position_qty += signed_qty

    #The mark_to_market() function updates the portfolio’s value using the latest market price and records it in the equity curve.
    def mark_to_market(self, price: float) -> None:
        """
        Updates the latest market price and records the portfolio's current equity in the equity curve.
        """
        self.state.last_price = price
        self.equity_curve.append(self.state.equity)
