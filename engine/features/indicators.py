def sma(values: list[float], window: int) -> list[float]:
    """
    Calculates the Simple Moving Average (SMA) over a list of values using a fixed window size.

    The SMA is computed by averaging the most recent `window` values at each position.
    For the first elements where there are not enough values to fill the window,
    the function returns 0.0.

    Example:
        values = [10, 20, 30, 40, 50]
        window = 3

        SMA calculation:
        [0.0, 0.0, (10+20+30)/3, (20+30+40)/3, (30+40+50)/3]
        → [0.0, 0.0, 20.0, 30.0, 40.0]

    Args:
        values: List of numeric values (e.g., price series).
        window: Number of periods used to compute the moving average.

    Returns:
        A list containing the SMA values for each index.
    """
    out: list[float] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(0.0)
        else:
            chunk = values[i + 1 - window : i + 1]
            out.append(sum(chunk) / window)
    return out