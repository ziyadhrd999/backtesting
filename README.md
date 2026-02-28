# Backtest Engine Template

This repository now follows a modular layout inspired by your proposed structure, with a notebook-first workflow plus reusable Python modules.

## Project layout

- `configs/`: runtime configuration files
- `data/loaders/`: market data loader adapters (CSV, Parquet, crypto API stub)
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
pytest
python experiments/run_backtest.py  # uses configs/default.yaml
```

## Notebook flow

1. `notebooks/01_data_exploration.ipynb`
2. `notebooks/02_strategy_research.ipynb`
3. `notebooks/03_backtest.ipynb`
4. `notebooks/04_parameter_search.ipynb`

## Notes

- The engine is intentionally lightweight and composable so you can swap in richer models incrementally.
- Existing `backtest_engine_template.ipynb` is kept as a standalone all-in-one reference.


## Dev update

- `experiments/run_backtest.py` now reads engine/strategy settings from `configs/default.yaml`.
- Strategy selection is centralized in `strategies/factory.py`.
