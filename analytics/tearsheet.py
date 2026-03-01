from engine.core.event import FillEvent

from analytics.extended import make_tearsheet_extended


def make_tearsheet(equity_curve: list[float], annualization: int = 252) -> dict[str, float]:
    """Return backward-compatible core tearsheet metrics.

    Args:
        equity_curve: Strategy equity values ordered in time.
        annualization: Number of periods per year used by annualized metrics.

    Returns:
        Dictionary containing only legacy keys:
        ``CAGR``, ``Sharpe``, ``MaxDrawdown``, and ``Calmar``.

    Example:
        >>> make_tearsheet([100_000, 101_000, 102_000], annualization=252)
        {'CAGR': ..., 'Sharpe': ..., 'MaxDrawdown': ..., 'Calmar': ...}
    """
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
    """Return extended tearsheet metrics for research workflows.

    Args:
        equity_curve: Strategy equity values ordered in time.
        annualization: Number of periods per year for annualization.
        fills: Optional fill history used for trade-level metrics.
        positions: Optional position quantity series.
        prices: Optional price series aligned with ``positions``.
        benchmark_equity: Optional benchmark equity curve.
        rolling_window: Window length for rolling Sharpe calculations.

    Returns:
        Dictionary containing core and extended analytics metrics.

    Example:
        >>> make_tearsheet_with_details([100, 101, 102], rolling_window=2)
        {'CAGR': ..., 'Sharpe': ..., 'NumTrades': ..., ...}
    """
    return make_tearsheet_extended(
        equity_curve=equity_curve,
        annualization=annualization,
        fills=fills,
        positions=positions,
        prices=prices,
        benchmark_equity=benchmark_equity,
        rolling_window=rolling_window,
    )
