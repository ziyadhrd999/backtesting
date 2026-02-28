import math


def equity_returns(equity_curve: list[float]) -> list[float]:
    if len(equity_curve) < 2:
        return []
    out = []
    for i in range(1, len(equity_curve)):
        prev = equity_curve[i - 1]
        out.append((equity_curve[i] / prev) - 1 if prev else 0.0)
    return out


def cagr(equity_curve: list[float], annualization: int = 252) -> float:
    if len(equity_curve) < 2:
        return 0.0
    total_return = equity_curve[-1] / equity_curve[0] - 1
    years = max((len(equity_curve) - 1) / annualization, 1 / annualization)
    return (1 + total_return) ** (1 / years) - 1


def sharpe_ratio(equity_curve: list[float], annualization: int = 252) -> float:
    rets = equity_returns(equity_curve)
    if not rets:
        return 0.0
    mu = sum(rets) / len(rets)
    var = sum((r - mu) ** 2 for r in rets) / len(rets)
    vol = math.sqrt(var) * math.sqrt(annualization)
    if vol == 0:
        return 0.0
    return (mu * annualization) / vol
