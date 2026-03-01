from __future__ import annotations

from collections import defaultdict
from math import sqrt

from analytics.drawdown import drawdown_series, max_drawdown
from analytics.performance import cagr, equity_returns, sharpe_ratio
from analytics.risk_metrics import calmar_ratio
from engine.core.event import FillEvent


def rolling_sharpe(equity_curve: list[float], window: int = 20, annualization: int = 252) -> list[float]:
    """Compute rolling Sharpe values from an equity curve."""
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
    """Return max/avg drawdown duration measured in bars."""
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
    """Simple turnover proxy as traded notional over average equity."""
    if not fills or not equity_curve:
        return 0.0
    traded_notional = sum(abs(f.fill_price * f.quantity) for f in fills)
    avg_equity = sum(equity_curve) / len(equity_curve)
    if avg_equity == 0:
        return 0.0
    return traded_notional / avg_equity


def exposure_metrics(positions: list[float], prices: list[float], equity_curve: list[float]) -> dict[str, float]:
    """Compute average and peak absolute exposure."""
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
    """Create basic round-trip trade records from fills."""
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
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if float(t["pnl"]) > 0)
    return wins / len(trades)


def benchmark_comparison(strategy_equity: list[float], benchmark_equity: list[float], annualization: int = 252) -> dict[str, float]:
    """Return active-return stats vs benchmark."""
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
    """Extended tearsheet that preserves core metrics and adds richer analytics."""
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
