from engine.core.event import FillEvent

from analytics.extended import make_tearsheet_extended


def make_tearsheet(equity_curve: list[float], annualization: int = 252) -> dict[str, float]:
    """Backward-compatible core tearsheet metrics."""
    metrics = make_tearsheet_extended(equity_curve=equity_curve, annualization=annualization)
    return {
        "CAGR": float(metrics["CAGR"]),
        "Sharpe": float(metrics["Sharpe"]),
        "MaxDrawdown": float(metrics["MaxDrawdown"]),
        "Calmar": float(metrics["Calmar"]),
    }


def make_tearsheet_with_details(
    equity_curve: list[float],
    annualization: int = 252,
    fills: list[FillEvent] | None = None,
    positions: list[float] | None = None,
    prices: list[float] | None = None,
    benchmark_equity: list[float] | None = None,
    rolling_window: int = 20,
) -> dict[str, float | int]:
    """Rich tearsheet metrics for Phase 4 workflows."""
    return make_tearsheet_extended(
        equity_curve=equity_curve,
        annualization=annualization,
        fills=fills,
        positions=positions,
        prices=prices,
        benchmark_equity=benchmark_equity,
        rolling_window=rolling_window,
    )
