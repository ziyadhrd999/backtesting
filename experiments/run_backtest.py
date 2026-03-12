import csv
import json
import platform
from datetime import timezone, datetime
from pathlib import Path
from subprocess import CalledProcessError, check_output

from analytics.tearsheet import make_tearsheet_with_details
from data.loaders import load_csv, load_yfinance
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.utils.config import load_yaml
from strategies.factory import build_strategy


ROOT = Path(__file__).resolve().parents[1]


def _symbols_from_data_cfg(data_cfg: dict) -> list[str]:
    """Resolve and filter configured symbols for a run.

    Supports either ``symbol`` (single) or ``symbols`` (list) and optional
    universe controls via ``include_symbols``, ``exclude_symbols``, and
    ``max_symbols``.
    """
    raw_symbols = data_cfg.get("symbols")
    symbols: list[str]
    if isinstance(raw_symbols, list):
        symbols = [str(symbol).strip() for symbol in raw_symbols if str(symbol).strip()]
    else:
        single = str(data_cfg.get("symbol", "NVDA")).strip()
        symbols = [single] if single else []

    include_symbols = data_cfg.get("include_symbols")
    if isinstance(include_symbols, list) and include_symbols:
        include_set = {str(symbol).strip() for symbol in include_symbols if str(symbol).strip()}
        symbols = [symbol for symbol in symbols if symbol in include_set]

    exclude_symbols = data_cfg.get("exclude_symbols")
    if isinstance(exclude_symbols, list) and exclude_symbols:
        exclude_set = {str(symbol).strip() for symbol in exclude_symbols if str(symbol).strip()}
        symbols = [symbol for symbol in symbols if symbol not in exclude_set]

    max_symbols = data_cfg.get("max_symbols")
    if max_symbols is not None:
        try:
            max_n = max(0, int(max_symbols))
            symbols = symbols[:max_n]
        except (TypeError, ValueError):
            pass

    seen: set[str] = set()
    unique: list[str] = []
    for symbol in symbols:
        if symbol in seen:
            continue
        seen.add(symbol)
        unique.append(symbol)
    return unique


def load_bars(data_cfg: dict) -> list:
    """Load market bars from configured data source.

    Supports ``yfinance`` and ``csv`` source types and returns engine-compatible
    market bar events.

    Args:
        data_cfg: Data configuration mapping (source, symbol, period/interval,
            path, etc.).

    Returns:
        List of market bars.

    Raises:
        ValueError: If the ``source`` value is unsupported.

    Example:
        >>> load_bars({'source': 'csv', 'path': 'data.csv', 'symbol': 'S'})
        [...]
    """
    source = str(data_cfg.get("source", "yfinance")).lower().strip()

    if source == "yfinance":
        symbols = _symbols_from_data_cfg(data_cfg)
        all_bars: list = []
        for symbol in symbols:
            all_bars.extend(
                load_yfinance(
                    symbol=symbol,
                    period=str(data_cfg.get("period", "2y")),
                    interval=str(data_cfg.get("interval", "1d")),
                    auto_adjust=bool(data_cfg.get("auto_adjust", True)),
                )
            )
        return sorted(all_bars, key=lambda bar: (bar.timestamp, bar.symbol))

    if source == "csv":
        csv_path = Path(data_cfg["path"])
        return load_csv(path=str(csv_path), symbol=str(data_cfg.get("symbol", "CSV")))

    raise ValueError(f"Unsupported data source: {source}")


def _git_commit() -> str:
    """Return current Git commit SHA for this repository.

    The function executes ``git rev-parse HEAD`` in repository root and returns
    the hash string. If Git is unavailable or the command fails, it returns the
    fallback value ``"unknown"``.

    Returns:
        Current commit hash string, or ``"unknown"`` when unavailable.

    Example:
        >>> isinstance(_git_commit(), str)
        True
    """
    try:
        return check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (CalledProcessError, FileNotFoundError):
        return "unknown"


def _persist_run(
    cfg: dict,
    metrics: dict,
    timestamps: list[str],
    equity_curve: list[float],
    fills: list,
    positions: list[float],
    cash_series: list[float],
    positions_by_symbol: list[dict[str, float | str]],
    portfolio_history: list[dict[str, float | str]],
    journal: list[dict[str, float | str]],
    trade_attribution: list[dict[str, float | str]],
) -> Path:
    """Persist experiment artifacts to disk.

    Writes config snapshot, summary metrics, run metadata, equity curve,
    fill-level data, and position/cash time series into a timestamped run
    directory under ``artifacts/runs``.

    Args:
        cfg: Full resolved runtime config.
        metrics: Scalar performance/risk metrics.
        timestamps: Bar timestamps aligned with position/cash series.
        equity_curve: Equity values across the run.
        fills: Fill event list.
        positions: Position quantity series.
        cash_series: Cash balance series.

    Returns:
        Path to the created run directory.

    Example:
        >>> isinstance(_persist_run({}, {}, [], [], [], [], []), Path)
        True
    """
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    strategy_name = str(cfg.get("strategy", {}).get("name", "strategy"))
    run_dir = ROOT / "artifacts" / "runs" / f"{run_id}_{strategy_name}"
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "config.snapshot.json").write_text(json.dumps(cfg, indent=2), encoding="utf-8")
    (run_dir / "metrics.summary.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    run_meta = {
        "run_id": run_id,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "python": platform.python_version(),
    }
    (run_dir / "run_meta.json").write_text(json.dumps(run_meta, indent=2), encoding="utf-8")

    with (run_dir / "equity_curve.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["index", "equity"])
        for i, equity in enumerate(equity_curve):
            writer.writerow([i, equity])

    with (run_dir / "fills.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "symbol", "side", "quantity", "fill_price", "fee"])
        for f in fills:
            writer.writerow([f.timestamp, f.symbol, f.side, f.quantity, f.fill_price, f.fee])

    with (run_dir / "positions.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "position_qty", "cash"])
        for ts, qty, cash in zip(timestamps, positions, cash_series):
            writer.writerow([ts, qty, cash])


    with (run_dir / "positions_by_symbol.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow([
            "timestamp",
            "symbol",
            "quantity",
            "avg_cost",
            "last_price",
            "market_value",
            "realized_pnl",
            "unrealized_pnl",
            "total_pnl",
            "fees_paid",
            "financing_paid",
        ])
        for row in positions_by_symbol:
            writer.writerow([
                row.get("timestamp", ""),
                row.get("symbol", ""),
                row.get("quantity", 0.0),
                row.get("avg_cost", 0.0),
                row.get("last_price", 0.0),
                row.get("market_value", 0.0),
                row.get("realized_pnl", 0.0),
                row.get("unrealized_pnl", 0.0),
                row.get("total_pnl", 0.0),
                row.get("fees_paid", 0.0),
                row.get("financing_paid", 0.0),
            ])

    with (run_dir / "portfolio_history.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "cash", "equity", "gross_exposure", "net_exposure"])
        for row in portfolio_history:
            writer.writerow([
                row.get("timestamp", ""),
                row.get("cash", 0.0),
                row.get("equity", 0.0),
                row.get("gross_exposure", 0.0),
                row.get("net_exposure", 0.0),
            ])

    with (run_dir / "ledger_journal.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "symbol", "entry_type", "amount", "details"])
        for row in journal:
            writer.writerow([
                row.get("timestamp", ""),
                row.get("symbol", ""),
                row.get("entry_type", ""),
                row.get("amount", 0.0),
                row.get("details", ""),
            ])

    with (run_dir / "trade_attribution.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["timestamp", "symbol", "closed_qty", "realized_pnl", "fill_price", "avg_cost_before"])
        for row in trade_attribution:
            writer.writerow([
                row.get("timestamp", ""),
                row.get("symbol", ""),
                row.get("closed_qty", 0.0),
                row.get("realized_pnl", 0.0),
                row.get("fill_price", 0.0),
                row.get("avg_cost_before", 0.0),
            ])

    return run_dir


if __name__ == "__main__":
    config_path = ROOT / "configs" / "default.yaml"
    cfg = load_yaml(config_path)

    engine_cfg = EngineConfig(
        initial_cash=float(cfg["engine"]["initial_cash"]),
        fee_bps=float(cfg["engine"]["fee_bps"]),
        slippage_bps=float(cfg["engine"]["slippage_bps"]),
        spread_bps=float(cfg["engine"].get("spread_bps", 1.0)),
        latency_bars=int(cfg["engine"].get("latency_bars", 0)),
        max_abs_weight=float(cfg["engine"].get("max_abs_weight", 1.0)),
        max_turnover_qty=cfg["engine"].get("max_turnover_qty"),
        max_notional=cfg["engine"].get("max_notional"),
        max_abs_exposure=cfg["engine"].get("max_abs_exposure"),
        allow_short=bool(cfg["engine"].get("allow_short", False)),
        borrow_rate_bps=float(cfg["engine"].get("borrow_rate_bps", 0.0)),
        financing_bars_per_year=int(cfg["engine"].get("financing_bars_per_year", 252)),
        stop_loss_mode=cfg["engine"].get("stop_loss_mode"),
        stop_loss_value=cfg["engine"].get("stop_loss_value"),
        stop_cooldown_bars=int(cfg["engine"].get("stop_cooldown_bars", 0)),
        max_trades_per_day=cfg["engine"].get("max_trades_per_day"),
        trade_cap_side=str(cfg["engine"].get("trade_cap_side", "both")),
    )

    strategy_cfg = cfg.get("strategy", {})
    strategy = build_strategy(strategy_cfg.get("name", "moving_average"), strategy_cfg)

    bars = load_bars(cfg.get("data", {}))
    if not bars:
        raise RuntimeError("No bars were loaded. Check your data config.")

    benchmark_cfg = cfg.get("benchmark")
    benchmark_equity: list[float] | None = None
    if benchmark_cfg and bool(benchmark_cfg.get("enabled", False)):
        benchmark_bars = load_bars(benchmark_cfg.get("data", {}))
        if benchmark_bars:
            bh_engine = BacktestEngine(
                EngineConfig(
                    initial_cash=engine_cfg.initial_cash,
                    fee_bps=0.0,
                    slippage_bps=0.0,
                    spread_bps=0.0,
                )
            )

            class BuyAndHold:
                """Simple benchmark strategy that always targets full long exposure.

                Example:
                    >>> BuyAndHold().on_bars({"S": object()})
                    {'S': 1.0}
                """

                def on_bars(self, bars_by_symbol) -> dict[str, float]:
                    """Return constant target weight for each symbol in the snapshot.

                    Args:
                        bars_by_symbol: Bars keyed by symbol.

                    Returns:
                        Symbol-keyed constant target weight ``1.0``.
                    """
                    return {symbol: 1.0 for symbol in bars_by_symbol}

            benchmark_equity = bh_engine.run(benchmark_bars, BuyAndHold())

    engine = BacktestEngine(engine_cfg)
    result = engine.run_detailed(bars, strategy)
    prices = [bar.close for bar in bars][: len(result.positions)]

    metrics = make_tearsheet_with_details(
        result.equity_curve,
        annualization=int(cfg["engine"].get("annualization", 252)),
        fills=result.fills,
        positions=result.positions,
        prices=prices,
        benchmark_equity=benchmark_equity,
        rolling_window=int(cfg.get("analytics", {}).get("rolling_window", 20)),
    )

    run_dir = _persist_run(
        cfg=cfg,
        metrics=metrics,
        timestamps=result.timestamps,
        equity_curve=result.equity_curve,
        fills=result.fills,
        positions=result.positions,
        cash_series=result.cash_series,
        positions_by_symbol=result.positions_by_symbol,
        portfolio_history=result.portfolio_history,
        journal=result.journal,
        trade_attribution=result.trade_attribution,
    )

    print(metrics)
    print(f"Run artifacts written to: {run_dir}")
