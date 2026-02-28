def drawdown_series(equity_curve: list[float]) -> list[float]:
    peak = float("-inf")
    out = []
    for x in equity_curve:
        peak = max(peak, x)
        out.append((x / peak) - 1 if peak > 0 else 0.0)
    return out


def max_drawdown(equity_curve: list[float]) -> float:
    dd = drawdown_series(equity_curve)
    return min(dd) if dd else 0.0
