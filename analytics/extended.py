from __future__ import annotations

from collections import defaultdict
from math import sqrt

from analytics.drawdown import drawdown_series, max_drawdown
from analytics.performance import cagr, equity_returns, sharpe_ratio
from analytics.risk_metrics import calmar_ratio
from engine.core.event import FillEvent


def rolling_sharpe(equity_curve: list[float], window: int = 20, annualization: int = 252) -> list[float]:
    """Compute rolling Sharpe ratio values from an equity curve.

    The function converts the input equity curve into periodic returns, then
    computes a Sharpe ratio over every rolling window of returns.

    Args:
        equity_curve: Portfolio equity values ordered in time.
        window: Rolling window size in return observations.
        annualization: Number of periods per year for annualization.

    Returns:
        List of rolling Sharpe values. Returns an empty list when there is not
        enough data to fill a window.

    Example:
        >>> rolling_sharpe([100, 101, 100, 102], window=2, annualization=252)
        [...]
    """
    rets = equity_returns(equity_curve)
    if window <= 1 or len(rets) < window:
        return []

    out: list[float] = []
    for i in range(window, len(rets) + 1):
        chunk = rets[i - window : i]
        mu = sum(chunk) / window
        var = sum((r - mu) ** 2 for r in chunk) / window
        vol = sqrt(var) * sqrt(annualization)
        out.append((mu * annualization) / vol if vol else 0.0)
    return out


def drawdown_duration(equity_curve: list[float]) -> dict[str, float]:
    """Compute drawdown duration statistics in bars.

    A drawdown duration is the length of a contiguous period where drawdown is
    below zero (i.e., equity remains under the previous peak).

    Args:
        equity_curve: Portfolio equity values ordered in time.

    Returns:
        Dictionary with:
        - ``MaxDrawdownDurationBars``: longest drawdown streak length.
        - ``AvgDrawdownDurationBars``: average drawdown streak length.

    Example:
        >>> drawdown_duration([100, 110, 105, 103, 111])
        {'MaxDrawdownDurationBars': 2.0, 'AvgDrawdownDurationBars': 2.0}
    """
    dd = drawdown_series(equity_curve)
    if not dd:
        return {"MaxDrawdownDurationBars": 0.0, "AvgDrawdownDurationBars": 0.0}

    durations: list[int] = []
    current = 0
    for v in dd:
        if v < 0:
            current += 1
        elif current > 0:
            durations.append(current)
            current = 0
    if current > 0:
        durations.append(current)

    if not durations:
        return {"MaxDrawdownDurationBars": 0.0, "AvgDrawdownDurationBars": 0.0}

    return {
        "MaxDrawdownDurationBars": float(max(durations)),
        "AvgDrawdownDurationBars": float(sum(durations) / len(durations)),
    }


def turnover_from_fills(fills: list[FillEvent], equity_curve: list[float]) -> float:
    """Estimate turnover from fills and equity.

    Turnover is computed as total traded notional divided by average equity.
    This provides a simple normalized activity measure.

    Args:
        fills: Executed fill events.
        equity_curve: Portfolio equity values ordered in time.

    Returns:
        Scalar turnover estimate. Returns 0.0 when fills/equity are unavailable
        or average equity is zero.

    Example:
        >>> turnover_from_fills([], [100_000, 101_000])
        0.0
    """
    if not fills or not equity_curve:
        return 0.0
    traded_notional = sum(abs(f.fill_price * f.quantity) for f in fills)
    avg_equity = sum(equity_curve) / len(equity_curve)
    if avg_equity == 0:
        return 0.0
    return traded_notional / avg_equity


def exposure_metrics(positions: list[float], prices: list[float], equity_curve: list[float]) -> dict[str, float]:
    """Compute average and peak absolute exposure.

    Exposure is estimated per bar as ``abs(position * price) / abs(equity)``.

    Args:
        positions: Position quantity by bar.
        prices: Price by bar aligned with ``positions``.
        equity_curve: Equity by bar aligned with ``positions``.

    Returns:
        Dictionary with:
        - ``AvgAbsExposure``: mean absolute exposure.
        - ``PeakAbsExposure``: maximum absolute exposure.

    Example:
        >>> exposure_metrics([10, 10], [100, 110], [1000, 1100])
        {'AvgAbsExposure': ..., 'PeakAbsExposure': ...}
    """
    n = min(len(positions), len(prices), len(equity_curve))
    if n == 0:
        return {"AvgAbsExposure": 0.0, "PeakAbsExposure": 0.0}

    exposures: list[float] = []
    for i in range(n):
        eq = equity_curve[i]
        if eq == 0:
            exposures.append(0.0)
        else:
            exposures.append(abs(positions[i] * prices[i]) / abs(eq))

    return {
        "AvgAbsExposure": sum(exposures) / len(exposures),
        "PeakAbsExposure": max(exposures),
    }


def trade_list_from_fills(fills: list[FillEvent]) -> list[dict[str, float | str]]:
    """Build a basic round-trip trade list from fill events.

    Fills are grouped by symbol and processed chronologically to detect simple
    open-to-flat round trips. Each closed trade record includes entry/exit
    timestamps, quantity, and realized PnL.

    Args:
        fills: Fill events in chronological order.

    Returns:
        List of trade dictionaries containing ``symbol``, ``entry_timestamp``,
        ``exit_timestamp``, ``quantity``, and ``pnl``.

    Example:
        >>> fills = [
        ...     FillEvent(timestamp='t0', symbol='S', side='BUY', quantity=1, fill_price=100, fee=0),
        ...     FillEvent(timestamp='t1', symbol='S', side='SELL', quantity=1, fill_price=101, fee=0),
        ... ]
        >>> trade_list_from_fills(fills)[0]['pnl']
        1.0
    """
    if not fills:
        return []

    grouped: dict[str, list[FillEvent]] = defaultdict(list)
    for fill in fills:
        grouped[fill.symbol].append(fill)

    trades: list[dict[str, float | str]] = []
    for symbol, sym_fills in grouped.items():
        qty = 0.0
        avg_price = 0.0
        fees = 0.0
        entry_time = ""

        for fill in sym_fills:
            signed_qty = fill.quantity if fill.side == "BUY" else -fill.quantity
            if qty == 0 and signed_qty != 0:
                entry_time = fill.timestamp

            if qty + signed_qty == 0 and qty != 0:
                realized = (fill.fill_price - avg_price) * qty - fees - fill.fee
                trades.append(
                    {
                        "symbol": symbol,
                        "entry_timestamp": entry_time,
                        "exit_timestamp": fill.timestamp,
                        "quantity": abs(qty),
                        "pnl": realized,
                    }
                )
                qty = 0.0
                avg_price = 0.0
                fees = 0.0
                continue

            if signed_qty > 0:
                new_qty = qty + signed_qty
                avg_price = ((avg_price * qty) + (fill.fill_price * signed_qty)) / new_qty if new_qty else 0.0
                qty = new_qty
                fees += fill.fee
            else:
                qty += signed_qty
                fees += fill.fee

    return trades


def win_rate(trades: list[dict[str, float | str]]) -> float:
    """Calculate fraction of profitable trades.

    Args:
        trades: Trade dictionaries containing a numeric ``pnl`` field.

    Returns:
        Ratio in ``[0, 1]`` of trades with positive PnL.

    Example:
        >>> win_rate([{'pnl': 1.0}, {'pnl': -0.5}])
        0.5
    """
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if float(t["pnl"]) > 0)
    return wins / len(trades)


def benchmark_comparison(strategy_equity: list[float], benchmark_equity: list[float], annualization: int = 252) -> dict[str, float]:
    """Compute benchmark-relative performance statistics.

    Both curves are aligned to the shorter available length. Active returns are
    defined as strategy periodic returns minus benchmark periodic returns.

    Args:
        strategy_equity: Strategy equity curve.
        benchmark_equity: Benchmark equity curve.
        annualization: Periods per year for annualization.

    Returns:
        Dictionary with benchmark CAGR, active CAGR, tracking error, and
        information ratio.

    Example:
        >>> benchmark_comparison([100, 102], [100, 101], annualization=252)
        {'BenchmarkCAGR': ..., 'ActiveCAGR': ..., 'TrackingError': ..., 'InformationRatio': ...}
    """
    n = min(len(strategy_equity), len(benchmark_equity))
    if n < 2:
        return {"BenchmarkCAGR": 0.0, "ActiveCAGR": 0.0, "TrackingError": 0.0, "InformationRatio": 0.0}

    s_rets = equity_returns(strategy_equity[:n])
    b_rets = equity_returns(benchmark_equity[:n])
    active = [s - b for s, b in zip(s_rets, b_rets)]

    mean_active = sum(active) / len(active) if active else 0.0
    var_active = sum((x - mean_active) ** 2 for x in active) / len(active) if active else 0.0
    tracking_error = sqrt(var_active) * sqrt(annualization)

    return {
        "BenchmarkCAGR": cagr(benchmark_equity[:n], annualization=annualization),
        "ActiveCAGR": cagr(strategy_equity[:n], annualization=annualization)
        - cagr(benchmark_equity[:n], annualization=annualization),
        "TrackingError": tracking_error,
        "InformationRatio": (mean_active * annualization) / tracking_error if tracking_error else 0.0,
    }


def make_tearsheet_extended(
    equity_curve: list[float],
    annualization: int = 252,
    fills: list[FillEvent] | None = None,
    positions: list[float] | None = None,
    prices: list[float] | None = None,
    benchmark_equity: list[float] | None = None,
    rolling_window: int = 20,
) -> dict[str, float | int]:
    """Build a comprehensive tearsheet while preserving core metrics.

    This function starts with legacy core metrics (CAGR/Sharpe/MaxDrawdown/
    Calmar), then adds trade-level and path-dependent diagnostics such as
    turnover, win rate, rolling Sharpe summary, drawdown duration, exposure,
    and optional benchmark-relative metrics.

    Args:
        equity_curve: Strategy equity values ordered in time.
        annualization: Number of periods per year.
        fills: Optional executed fills for trade/turnover metrics.
        positions: Optional position series for exposure metrics.
        prices: Optional price series aligned with ``positions``.
        benchmark_equity: Optional benchmark equity curve.
        rolling_window: Window length used for rolling Sharpe computation.

    Returns:
        Dictionary of scalar tearsheet metrics.

    Example:
        >>> make_tearsheet_extended([100, 101, 102], annualization=252)
        {'CAGR': ..., 'Sharpe': ..., 'MaxDrawdown': ..., 'Calmar': ..., ...}
    """
    fills = fills or []
    positions = positions or []
    prices = prices or []

    metrics: dict[str, float | int] = {
        "CAGR": cagr(equity_curve, annualization=annualization),
        "Sharpe": sharpe_ratio(equity_curve, annualization=annualization),
        "MaxDrawdown": max_drawdown(equity_curve),
        "Calmar": calmar_ratio(equity_curve, annualization=annualization),
    }

    trades = trade_list_from_fills(fills)
    roll = rolling_sharpe(equity_curve, window=rolling_window, annualization=annualization)

    metrics.update(
        {
            "NumTrades": len(trades),
            "WinRate": win_rate(trades),
            "Turnover": turnover_from_fills(fills, equity_curve),
            "RollingSharpeMean": (sum(roll) / len(roll)) if roll else 0.0,
            "RollingSharpeLast": roll[-1] if roll else 0.0,
        }
    )
    metrics.update(drawdown_duration(equity_curve))
    metrics.update(exposure_metrics(positions=positions, prices=prices, equity_curve=equity_curve))

    if benchmark_equity is not None:
        metrics.update(benchmark_comparison(equity_curve, benchmark_equity, annualization=annualization))

    return metrics
