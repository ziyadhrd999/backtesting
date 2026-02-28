def pct_change(values: list[float]) -> list[float]:
    """
    Calculates the percentage change between consecutive values in a list.

    The percentage change measures how much a value has increased or decreased
    relative to the previous value. The first element is set to 0.0 since there
    is no previous value to compare.

    Formula:
        pct_change = (current_value / previous_value) - 1

    Example:
        values = [100, 105, 110]

        Calculations:
        first value → 0.0
        (105 / 100) - 1 = 0.05
        (110 / 105) - 1 ≈ 0.0476

        Result:
        [0.0, 0.05, 0.0476]

    Args:
        values: List of numeric values (e.g., prices).

    Returns:
        A list containing the percentage change for each value compared to the previous one.
    """
    if not values:
        return []
    out = [0.0]
    for i in range(1, len(values)):
        prev = values[i - 1]
        out.append((values[i] / prev) - 1 if prev else 0.0)
    return out