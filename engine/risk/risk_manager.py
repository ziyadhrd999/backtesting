def clamp_weight(target_weight: float, max_abs_weight: float = 1.0) -> float:
    """Clamp target portfolio weight to ``[-max_abs_weight, +max_abs_weight]``."""
    return max(-max_abs_weight, min(max_abs_weight, target_weight))


def apply_turnover_limit(target_qty: float, current_qty: float, max_turnover_qty: float | None) -> float:
    """Limit per-bar position change in absolute units.

    If ``max_turnover_qty`` is set, the function caps ``target_qty - current_qty`` to that
    absolute amount while preserving direction.
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
    """Cap absolute position notional by limiting quantity at current price.

    ``max_notional`` is interpreted as ``abs(quantity) * price``.
    """
    if max_notional is None or max_notional <= 0 or price <= 0:
        return target_qty

    max_qty = max_notional / price
    return max(-max_qty, min(max_qty, target_qty))


def apply_max_exposure(target_weight: float, max_abs_exposure: float | None) -> float:
    """Cap absolute target exposure (weight) before position sizing."""
    if max_abs_exposure is None or max_abs_exposure <= 0:
        return target_weight
    return clamp_weight(target_weight, max_abs_weight=max_abs_exposure)
