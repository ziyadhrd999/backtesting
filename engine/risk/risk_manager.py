def clamp_weight(target_weight: float, max_abs_weight: float = 1.0) -> float:
    """Clamp a target portfolio weight to symmetric bounds.

    Args:
        target_weight: Desired portfolio weight (can be outside bounds).
        max_abs_weight: Maximum allowed absolute weight.

    Returns:
        Weight constrained to ``[-max_abs_weight, +max_abs_weight]``.

    Example:
        >>> clamp_weight(1.5, max_abs_weight=1.0)
        1.0
        >>> clamp_weight(-1.2, max_abs_weight=1.0)
        -1.0
    """
    return max(-max_abs_weight, min(max_abs_weight, target_weight))


def apply_turnover_limit(target_qty: float, current_qty: float, max_turnover_qty: float | None) -> float:
    """Cap per-bar quantity change to reduce trading churn.

    Args:
        target_qty: Desired absolute position after rebalancing.
        current_qty: Current position quantity.
        max_turnover_qty: Maximum allowed absolute quantity change per bar.
            If ``None`` or non-positive, no turnover cap is applied.

    Returns:
        A quantity that respects the per-bar turnover limit.

    Example:
        >>> apply_turnover_limit(target_qty=10, current_qty=0, max_turnover_qty=3)
        3
        >>> apply_turnover_limit(target_qty=-8, current_qty=0, max_turnover_qty=2)
        -2
    """
    if max_turnover_qty is None or max_turnover_qty <= 0:
        return target_qty

    delta = target_qty - current_qty
    if delta > max_turnover_qty:
        return current_qty + max_turnover_qty
    if delta < -max_turnover_qty:
        return current_qty - max_turnover_qty
    return target_qty


def apply_max_notional(target_qty: float, price: float, max_notional: float | None) -> float:
    """Cap position size using a maximum absolute notional.

    Args:
        target_qty: Desired position quantity.
        price: Current asset price.
        max_notional: Maximum allowed absolute notional ``abs(qty) * price``.
            If ``None`` or non-positive, no notional cap is applied.

    Returns:
        Quantity constrained by the notional limit.

    Example:
        >>> apply_max_notional(target_qty=20, price=100, max_notional=500)
        5.0
        >>> apply_max_notional(target_qty=-20, price=100, max_notional=500)
        -5.0
    """
    if max_notional is None or max_notional <= 0 or price <= 0:
        return target_qty

    max_qty = max_notional / price
    return max(-max_qty, min(max_qty, target_qty))


def apply_max_exposure(target_weight: float, max_abs_exposure: float | None) -> float:
    """Cap strategy exposure before converting weight to quantity.

    Args:
        target_weight: Strategy output exposure.
        max_abs_exposure: Maximum allowed absolute exposure. If ``None`` or
            non-positive, exposure is unchanged.

    Returns:
        Exposure constrained to ``[-max_abs_exposure, +max_abs_exposure]``.

    Example:
        >>> apply_max_exposure(0.8, max_abs_exposure=0.2)
        0.2
    """
    if max_abs_exposure is None or max_abs_exposure <= 0:
        return target_weight
    return clamp_weight(target_weight, max_abs_weight=max_abs_exposure)
