from analytics.drawdown import max_drawdown
from analytics.performance import cagr


def calmar_ratio(equity_curve: list[float], annualization: int = 252) -> float:
    mdd = abs(max_drawdown(equity_curve))
    if mdd == 0:
        return 0.0
    return cagr(equity_curve, annualization=annualization) / mdd
