from analytics.drawdown import max_drawdown
from analytics.performance import cagr, sharpe_ratio
from analytics.risk_metrics import calmar_ratio


def make_tearsheet(equity_curve: list[float], annualization: int = 252) -> dict[str, float]:
    return {
        "CAGR": cagr(equity_curve, annualization=annualization),
        "Sharpe": sharpe_ratio(equity_curve, annualization=annualization),
        "MaxDrawdown": max_drawdown(equity_curve),
        "Calmar": calmar_ratio(equity_curve, annualization=annualization),
    }
