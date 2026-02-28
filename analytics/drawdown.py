def drawdown_series(equity_curve: list[float]) -> list[float]:
    """
    Computes the drawdown series of a portfolio equity curve.

    Drawdown measures how much the portfolio value has fallen from its
    historical peak at each point in time.

    Formula:
        drawdown = (current_equity / peak_equity) - 1

    Example:
        equity_curve = [100000, 105000, 103000, 110000]

        Peak values:
        [100000, 105000, 105000, 110000]

        Drawdowns:
        [0.0, 0.0, (103000/105000 - 1), 0.0]
        → [0.0, 0.0, -0.0190, 0.0]

    Args:
        equity_curve: List of portfolio equity values over time.

    Returns:
        A list representing the drawdown at each time step.
    """
    peak = float("-inf")
    out = []
    for x in equity_curve:
        peak = max(peak, x)
        out.append((x / peak) - 1 if peak > 0 else 0.0)
    return out


def max_drawdown(equity_curve: list[float]) -> float:
    """
    Calculates the maximum drawdown of a portfolio equity curve.

    Maximum drawdown represents the largest percentage drop from a
    historical peak to a subsequent trough during the period.

    Example:
        equity_curve = [100000, 110000, 105000, 90000, 95000]

        Drawdowns:
        [0.0, 0.0, -0.045, -0.182, -0.136]

        max_drawdown = -0.182  → -18.2%

    Args:
        equity_curve: List of portfolio equity values over time.

    Returns:
        The maximum drawdown (most negative value) in the equity curve.
    """
    dd = drawdown_series(equity_curve)
    return min(dd) if dd else 0.0
