def clamp_weight(target_weight: float, max_abs_weight: float = 1.0) -> float:
    """
    Restricts a portfolio weight so it stays within a specified maximum absolute limit.

    The function "clamps" the weight to the range:
        [-max_abs_weight, +max_abs_weight]

    This prevents strategies from taking positions larger than the allowed leverage.

    Example:
        target_weight = 1.5
        max_abs_weight = 1.0

        Result:
        clamp_weight(1.5) → 1.0

        target_weight = -1.3
        clamp_weight(-1.3) → -1.0

        target_weight = 0.6
        clamp_weight(0.6) → 0.6

    Args:
        target_weight: Desired portfolio allocation weight produced by a strategy.
        max_abs_weight: Maximum allowed absolute portfolio weight (default = 1.0).

    Returns:
        A weight limited to the interval [-max_abs_weight, max_abs_weight].
    """
    return max(-max_abs_weight, min(max_abs_weight, target_weight))