def max_notional(equity: float, max_leverage: float) -> float:
    """
    Calculates the maximum allowable trade value (notional exposure) based on
    portfolio equity and the maximum permitted leverage.

    Notional exposure represents the total value of positions that the portfolio
    can control. Leverage allows the portfolio to take positions larger than the
    available equity.

    Formula:
        max_notional = equity * max_leverage

    Example:
        equity = 100,000
        max_leverage = 2.0

        max_notional = 100000 * 2.0
        max_notional = 200000

        This means the portfolio can control up to $200,000 worth of assets.

    Args:
        equity: Total portfolio value (cash + positions).
        max_leverage: Maximum allowed leverage multiplier.

    Returns:
        The maximum notional value of positions allowed in the portfolio.
    """
    return equity * max_leverage