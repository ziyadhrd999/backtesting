# Backtest Engine Template

This repository now follows a modular layout inspired by your proposed structure, with a notebook-first workflow plus reusable Python modules.

## Project layout

- `configs/`: runtime configuration files
- `data/loaders/`: market data loader adapters (CSV, yfinance)
- `engine/`: core event-driven backtest components
- `strategies/`: strategy interfaces and templates
- `analytics/`: performance and risk metric helpers
- `notebooks/`: research and backtest notebooks
- `experiments/`: runnable scripts for backtest, grid search, walk-forward
- `tests/`: unit tests for portfolio, execution, metrics

## Quickstart

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
pytest
python -m experiments.run_backtest  # uses configs/default.yaml
```

## Notebook flow

1. `notebooks/01_data_exploration.ipynb`
2. `notebooks/02_strategy_research.ipynb`
3. `notebooks/03_backtest.ipynb`
4. `notebooks/04_parameter_search.ipynb`

## Notes

- The engine is intentionally lightweight and composable so you can swap in richer models incrementally.
- Existing `backtest_engine_template.ipynb` is kept as a standalone all-in-one reference.


## Phase 4 workflow additions

- `experiments/run_backtest.py` now persists run artifacts (`config.snapshot.json`, `metrics.summary.json`, `equity_curve.csv`, `fills.csv`, `positions.csv`) under `artifacts/runs/...`.
- Extended analytics include trade count/win rate, exposure, turnover, rolling Sharpe summary, and drawdown duration.
- Optional benchmark comparison can be enabled in `configs/default.yaml`.
- `experiments/run_cost_sensitivity.py` sweeps fee/slippage/spread assumptions and prints comparative metrics.

## Experiments scripts explained

The `experiments/` directory contains independent runnable scripts. Each script has its own
`if __name__ == "__main__":` entry point because each one is a different workflow.

- `experiments/run_backtest.py`
  - Main configured backtest runner.
  - Loads config (`configs/default.yaml`), data, and strategy.
  - Optionally runs a benchmark (buy-and-hold) and computes extended analytics.
  - Persists artifacts under `artifacts/runs/...` (`config.snapshot.json`,
    `metrics.summary.json`, `equity_curve.csv`, `fills.csv`, `positions.csv`, `run_meta.json`).

- `experiments/run_grid_search.py`
  - Quick in-sample parameter sweep on synthetic data.
  - Tries MA parameter combinations and ranks by Sharpe.
  - Useful for rapid iteration, not final robust validation.

- `experiments/run_walkforward.py`
  - Walk-forward evaluation on synthetic regime-changing data.
  - Repeats train-then-test windows: optimize on train, evaluate on next test slice.
  - Helps check robustness and reduce overfitting risk.

- `experiments/run_cost_sensitivity.py`
  - Transaction-cost robustness study.
  - Sweeps fee/slippage/spread scenarios and reports comparative metrics.
  - Useful to understand how fragile strategy performance is to execution frictions.

Suggested workflow:
1. Start with `run_grid_search.py` for fast parameter intuition.
2. Use `run_walkforward.py` to validate time-split robustness.
3. Run `run_backtest.py` for a full tracked experiment with artifacts.
4. Run `run_cost_sensitivity.py` to test execution-cost resilience.

## Dev update

- `experiments/run_backtest.py` now reads engine/strategy settings from `configs/default.yaml` (including spread/slippage/fees).
- Strategy selection is centralized in `strategies/factory.py`.

## Phase 5 updates (multi-asset + cash-only execution)

- Strategy interface is now snapshot-based: strategies implement `on_bars(bars_by_symbol)` and return
  target weights as a dictionary `{symbol: weight}`.
- The engine now groups incoming bars by timestamp and rebalances using symbol baskets,
  instead of processing one symbol-bar signal at a time.
- Portfolio state is symbol-keyed (`positions`, `last_prices`) with per-symbol mark-to-market
  and aggregated equity.
- Built-in strategies (`moving_average`, `momentum`, `mean_reversion`) maintain per-symbol
  rolling buffers and emit per-symbol targets.
- Execution remains **cash-only** by default:
  - buy orders are checked against available cash at execution time,
  - oversized buy quantities are reduced to affordable size,
  - cash is prevented from going below zero due to buys.

Practical implication:
- This simulator is currently designed for cash-feasible strategy validation first.
- Leverage/margin behavior is intentionally not enabled in the default path.
