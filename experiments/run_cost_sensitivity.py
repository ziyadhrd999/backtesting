from itertools import product
from pathlib import Path

from analytics.tearsheet import make_tearsheet_with_details
from experiments.run_backtest import load_bars
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.utils.config import load_yaml
from strategies.factory import build_strategy


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    cfg = load_yaml(root / "configs" / "default.yaml")

    bars = load_bars(cfg.get("data", {}))
    strategy_cfg = cfg.get("strategy", {})

    rows = []
    for fee_bps, slippage_bps, spread_bps in product([0.0, 1.0, 2.0, 5.0], [0.0, 1.0, 2.0], [0.0, 1.0, 2.0]):
        strategy = build_strategy(strategy_cfg.get("name", "moving_average"), strategy_cfg)
        engine = BacktestEngine(
            EngineConfig(
                initial_cash=float(cfg["engine"]["initial_cash"]),
                fee_bps=fee_bps,
                slippage_bps=slippage_bps,
                spread_bps=spread_bps,
            )
        )
        result = engine.run_detailed(bars, strategy)
        metrics = make_tearsheet_with_details(
            result.equity_curve,
            annualization=int(cfg["engine"].get("annualization", 252)),
            fills=result.fills,
            positions=result.positions,
            prices=[b.close for b in bars][: len(result.positions)],
        )

        rows.append(
            {
                "fee_bps": fee_bps,
                "slippage_bps": slippage_bps,
                "spread_bps": spread_bps,
                "CAGR": metrics["CAGR"],
                "Sharpe": metrics["Sharpe"],
                "MaxDrawdown": metrics["MaxDrawdown"],
                "Turnover": metrics["Turnover"],
            }
        )

    rows.sort(key=lambda r: r["Sharpe"], reverse=True)
    for row in rows:
        print(row)
