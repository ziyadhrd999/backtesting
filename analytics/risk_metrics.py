from analytics.drawdown import max_drawdown
from analytics.performance import cagr


def calmar_ratio(equity_curve: list[float], annualization: int = 252) -> float:
    """
    Calculates the Calmar Ratio, a performance metric that measures return relative
    to maximum drawdown.

    The Calmar Ratio evaluates how much annual return a strategy generates for each
    unit of risk taken (measured by maximum drawdown).

    Formula:
        Calmar Ratio = CAGR / |Maximum Drawdown|

    Example:
        CAGR = 0.20  (20% annual return)
        max_drawdown = -0.10  (-10%)

        Calmar Ratio = 0.20 / 0.10
        Calmar Ratio = 2.0

        This means the strategy earns 2 units of return for each unit of drawdown risk.

    Args:
        equity_curve: List of portfolio equity values over time.
        annualization: Number of periods per year (default = 252 trading days).

    Returns:
        The Calmar Ratio of the strategy. Returns 0.0 if the maximum drawdown is zero.
    """
    mdd = abs(max_drawdown(equity_curve))
    if mdd == 0:
        return 0.0
    return cagr(equity_curve, annualization=annualization) / mdd
