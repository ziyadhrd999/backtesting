def sma(values: list[float], window: int) -> list[float]:
    out: list[float] = []
    for i in range(len(values)):
        if i + 1 < window:
            out.append(0.0)
        else:
            chunk = values[i + 1 - window : i + 1]
            out.append(sum(chunk) / window)
    return out
