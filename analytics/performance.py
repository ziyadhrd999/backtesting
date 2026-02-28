import math


def equity_returns(equity_curve: list[float]) -> list[float]:
    """
    Computes the periodic returns of a portfolio from its equity curve.

    The return at each step is calculated as the percentage change from the
    previous equity value.

    Formula:
        return = (current_equity / previous_equity) - 1

    Example:
        equity_curve = [100000, 105000, 110000]

        Returns:
        (105000 / 100000) - 1 = 0.05
        (110000 / 105000) - 1 ≈ 0.0476

        Result:
        [0.05, 0.0476]

    Args:
        equity_curve: List of portfolio equity values over time.

    Returns:
        A list of periodic returns corresponding to each time step.
    """
    if len(equity_curve) < 2:
        return []
    out = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        out.append((equity_curve[i] / prev) - 1 if prev else 0.0)
    return out


def cagr(equity_curve: list[float], annualization: int = 252) -> float:
    """
    Calculates the Compound Annual Growth Rate (CAGR) of a portfolio.

    CAGR represents the average annual growth rate of an investment over time,
    assuming profits are reinvested.

    Formula:
        CAGR = (Ending Value / Starting Value)^(1 / Years) - 1

    Example:
        equity_curve = [100000, 120000]

        total_return = 120000 / 100000 - 1 = 0.20
        years = 1

        CAGR = (1.20)^(1/1) - 1
        CAGR = 0.20  → 20%

    Args:
        equity_curve: List of portfolio equity values over time.
        annualization: Number of periods per year (default = 252 trading days).

    Returns:
        The compound annual growth rate of the portfolio.
    """    
    if len(equity_curve) < 2:
        return 0.0
    total_return = equity_curve[-1] / equity_curve[0] - 1
    years = max((len(equity_curve) - 1) / annualization, 1 / annualization)
    return (1 + total_return) ** (1 / years) - 1


def sharpe_ratio(equity_curve: list[float], annualization: int = 252) -> float:
    """
    Calculates the Sharpe Ratio, a measure of risk-adjusted return.

    The Sharpe Ratio compares the average return of a strategy to the
    volatility of its returns.

    Formula:
        Sharpe = (Mean Return × Annualization) / Annualized Volatility

    Example:
        mean_daily_return = 0.001
        daily_volatility = 0.01
        annualization = 252

        annual_return = 0.001 × 252 = 0.252
        annual_vol = 0.01 × sqrt(252) ≈ 0.1587

        Sharpe ≈ 0.252 / 0.1587 ≈ 1.59

    Args:
        equity_curve: List of portfolio equity values over time.
        annualization: Number of periods per year (default = 252 trading days).

    Returns:
        The Sharpe Ratio of the strategy. Returns 0.0 if volatility is zero.
    """
    rets = equity_returns(equity_curve)
    if not rets:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / len(rets)
    vol = math.sqrt(var) * math.sqrt(annualization)
    if vol == 0:
        return 0.0
    return (mu * annualization) / vol
