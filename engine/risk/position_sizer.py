def target_qty_from_weight(equity: float, price: float, target_weight: float) -> float:
    """
    Calculates the number of asset units required to achieve a target portfolio weight.

    The target quantity is determined by allocating a fraction of the portfolio's
    total equity to the asset and dividing by the asset price.

    Formula:
        target_quantity = (equity * target_weight) / price

    Example:
        equity = 100,000
        price = 50
        target_weight = 0.5   (50% of portfolio)

        target_quantity = (100000 * 0.5) / 50
        target_quantity = 1000

        So the portfolio should hold 1000 units of the asset.

    Args:
        equity: Total portfolio value (cash + positions).
        price: Current market price of the asset.
        target_weight: Desired portfolio allocation (-1.0 to 1.0).

    Returns:
        The quantity of the asset required to achieve the target weight.
        Returns 0.0 if the price is zero or negative to avoid division errors.
    """
    if price <= 0:
        return 0.0
    return (equity * target_weight) / price