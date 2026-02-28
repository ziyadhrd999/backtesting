from analytics.drawdown import max_drawdown
from analytics.performance import cagr


def test_metrics_on_simple_curve():
    curve = [100, 110, 105, 120]
    assert round(max_drawdown(curve), 4) == round((105 / 110) - 1, 4)
    assert cagr(curve, annualization=3) > 0
