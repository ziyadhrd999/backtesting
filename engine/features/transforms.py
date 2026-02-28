def pct_change(values: list[float]) -> list[float]:
    if not values:
        return []
    out = [0.0]
    for i in range(1, len(values)):
        prev = values[i - 1]
        out.append((values[i] / prev) - 1 if prev else 0.0)
    return out
