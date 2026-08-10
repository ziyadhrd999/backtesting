# Backtesting Project Documentation

Generated for repository: `ziyadhrd999/backtesting`  
Branch reviewed: `dev`  
Review date: 2026-08-10

## 1. Executive Summary

This project is a modular Python backtesting research framework for systematic trading strategies. It appears to have started as a notebook-first backtest engine template, then gradually evolved into a reusable, event-driven, multi-asset simulator with configurable execution realism, risk controls, accounting, analytics, experiment scripts, and research notebooks.

The core idea is not just "run a moving average strategy." The stronger vision is:

- load historical market data from CSV or yfinance,
- define strategies as target-weight generators,
- simulate realistic portfolio rebalancing across one or more symbols,
- model fees, slippage, spread, latency, long-only constraints, stop losses, trade caps, and optional shorting,
- record fills, equity, cash, positions, accounting journals, and attribution,
- evaluate strategy performance using a tearsheet of return, risk, turnover, drawdown, benchmark, and trade metrics,
- preserve experiment artifacts for later review.

In plain terms: this is a personal quantitative research lab for testing trading ideas in a structured way.

## 2. Reconstructed Original Vision

Based on the code, README, notebooks, experiment scripts, tests, and commit messages, the project likely moved through these phases:

### Phase 1: Notebook-First Prototype

The repository contains `backtest_engine_template.ipynb` and staged notebooks under `notebooks/`:

- `01_data_exploration.ipynb`
- `02_strategy_research.ipynb`
- `03_backtest.ipynb`
- `04_parameter_search.ipynb`

This suggests the initial goal was to explore trading logic interactively in notebooks before extracting reusable modules.

### Phase 2: Modular Backtest Engine

The codebase was then split into packages:

- `engine/` for simulation logic,
- `strategies/` for trading rules,
- `analytics/` for metrics,
- `data/` for loaders,
- `experiments/` for runnable workflows,
- `configs/` for reproducible settings,
- `tests/` for regression coverage.

This shifted the project from a one-off notebook into a maintainable research framework.

### Phase 3: Execution Realism and Risk Controls

The engine gained controls for:

- fee basis points,
- slippage basis points,
- spread basis points,
- order latency,
- maximum absolute weight,
- maximum turnover quantity,
- maximum notional exposure,
- maximum absolute exposure,
- optional short selling,
- borrow cost,
- stop-loss liquidation,
- stop-loss cooldown,
- maximum trades per day.

This shows an intent to avoid overly optimistic backtests and make the simulator more realistic.

### Phase 4: Analytics and Artifacts

The project added persistent outputs under `artifacts/runs/...`, including:

- config snapshot,
- summary metrics,
- run metadata,
- equity curve,
- fills,
- positions,
- cash series,
- positions by symbol,
- portfolio history,
- accounting journal,
- trade attribution.

This phase points toward reproducible experiments, auditability, and comparing runs over time.

### Phase 5: Multi-Asset Snapshot Engine

The latest important architecture change is multi-asset support:

- market events are grouped into timestamp baskets,
- strategies receive all available bars at a timestamp,
- strategies return `{symbol: target_weight}`,
- the engine rebalances across the symbol basket,
- portfolio state is keyed by symbol,
- accounting is tracked per symbol,
- cash-only long-only behavior is the default.

This means the project is now aimed at portfolio-style strategy research, not only single-instrument testing.

## 3. Repository Layout

```text
.
├── analytics/
│   ├── drawdown.py
│   ├── extended.py
│   ├── performance.py
│   ├── risk_metrics.py
│   └── tearsheet.py
├── configs/
│   ├── default.yaml
│   └── experiments/
│       └── ma_cross.yaml
├── data/
│   ├── loaders/
│   │   ├── csv_loader.py
│   │   └── yfinance_loader.py
│   └── stocks_csv/
│       └── NVDA_data.csv
├── engine/
│   ├── accounting/
│   │   └── ledger.py
│   ├── core/
│   │   ├── backtest_engine.py
│   │   ├── broker.py
│   │   ├── event.py
│   │   ├── order.py
│   │   └── portfolio.py
│   ├── execution/
│   │   ├── cost_model.py
│   │   ├── fill_model.py
│   │   ├── slippage.py
│   │   └── spread.py
│   ├── features/
│   │   ├── feature_store.py
│   │   ├── indicators.py
│   │   └── transforms.py
│   ├── risk/
│   │   ├── leverage.py
│   │   ├── position_sizer.py
│   │   └── risk_manager.py
│   └── utils/
│       ├── calendar.py
│       ├── config.py
│       ├── logging.py
│       └── validation.py
├── experiments/
│   ├── run_backtest.py
│   ├── run_cost_sensitivity.py
│   ├── run_grid_search.py
│   └── run_walkforward.py
├── notebooks/
├── strategies/
├── tests/
├── README.md
├── pyproject.toml
└── requirements.txt
```

## 4. Main User Workflow

The expected workflow is:

1. Configure a run in `configs/default.yaml`.
2. Choose data source and symbols.
3. Choose a strategy and parameters.
4. Run:

```bash
python -m experiments.run_backtest
```

5. Inspect printed metrics.
6. Review saved artifacts under `artifacts/runs/<timestamp>_<strategy>/`.
7. Iterate using notebooks or experiment scripts.

The README recommends this research loop:

1. Use `run_grid_search.py` for fast parameter intuition.
2. Use `run_walkforward.py` to test time-split robustness.
3. Use `run_backtest.py` for a full tracked experiment.
4. Use `run_cost_sensitivity.py` to test whether results survive execution costs.

## 5. Installation and Setup

The project is a Python package with editable install support.

Recommended setup:

```bash
python -m venv .venv
```

On Linux/macOS:

```bash
source .venv/bin/activate
```

On Windows PowerShell:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\.venv\Scripts\Activate.ps1
```

Then:

```bash
pip install -r requirements.txt
pip install -e .
pytest
```

Dependencies listed in `requirements.txt`:

- `pandas`
- `numpy`
- `matplotlib`
- `pyyaml`
- `pytest`
- `jupyterlab`
- `yfinance`

The package metadata in `pyproject.toml` names the project `backtest-engine-template` and requires Python `>=3.10`.

## 6. Configuration

The default runtime config is `configs/default.yaml`.

Current default engine settings:

```yaml
engine:
  initial_cash: 100000
  fee_bps: 0.25
  slippage_bps: 1.0
  spread_bps: 0.5
  annualization: 252
  latency_bars: 0
  max_abs_weight: 2.0
  allow_short: false
  borrow_rate_bps: 0.2
  financing_bars_per_year: 252
  stop_loss_mode: pct
  stop_loss_value: 0.05
  stop_cooldown_bars: 5
  max_trades_per_day: 5
  trade_cap_side: buy
```

Current default strategy:

```yaml
strategy:
  name: moving_average
  fast_window: 20
  slow_window: 100
```

Current default data:

```yaml
data:
  source: yfinance
  symbols: [NVDA, MSFT, AAPL]
  max_symbols: 3
  period: 2y
  interval: 60m
  auto_adjust: true
```

Optional benchmark support exists but is currently disabled:

```yaml
benchmark:
  enabled: false
  data:
    source: yfinance
    symbol: SPY
    period: 2y
    interval: 1d
    auto_adjust: true
```

The loader supports both `symbol` and `symbols`. It also supports:

- `include_symbols`
- `exclude_symbols`
- `max_symbols`

This is useful for testing a subset of a larger universe.

## 7. Core Architecture

### 7.1 Market Data Model

The central market data object is `MarketEvent` in `engine/core/event.py`.

It represents an OHLCV bar:

- `timestamp`
- `symbol`
- `open`
- `high`
- `low`
- `close`
- `volume`

Only `timestamp`, `symbol`, and `close` are required. If `open`, `high`, `low`, or `volume` are omitted, the object fills them with sensible defaults.

### 7.2 Strategy Interface

All strategies implement:

```python
def on_bars(self, bars_by_symbol: dict[str, MarketEvent]) -> dict[str, float]:
    ...
```

Input:

- all market bars available at one timestamp, keyed by symbol.

Output:

- desired target portfolio weights, keyed by symbol.

Example output:

```python
{
    "NVDA": 0.5,
    "MSFT": 0.3,
    "AAPL": 0.0,
}
```

The engine interprets missing symbols as target weight `0.0` when a current bar exists, which can flatten positions.

### 7.3 Backtest Engine

The main engine is `BacktestEngine` in `engine/core/backtest_engine.py`.

Its process is:

1. Sort or receive bars ordered by timestamp.
2. Group bars into timestamp baskets.
3. Mark portfolio to market.
4. Execute ready pending orders.
5. Mark portfolio again after execution.
6. Ask strategy for target weights.
7. Apply risk constraints.
8. Convert target weights to target quantities.
9. Create rebalance orders.
10. Queue orders according to latency.
11. Track positions, cash, timestamps, ledger, and equity.
12. Return a `RunResult`.

### 7.4 Result Object

`run_detailed()` returns a `RunResult` containing:

- `equity_curve`
- `fills`
- `positions`
- `cash_series`
- `timestamps`
- `positions_by_symbol`
- `portfolio_history`
- `journal`
- `trade_attribution`

The simpler `run()` method returns only the equity curve.

## 8. Execution Model

Execution is handled by:

- `engine/core/broker.py`
- `engine/execution/fill_model.py`
- `engine/execution/slippage.py`
- `engine/execution/spread.py`
- `engine/execution/cost_model.py`

Supported order types:

- `MARKET`
- `LIMIT`
- `STOP`

Fill behavior:

- market orders fill at bar close,
- limit orders fill if touched by bar high/low,
- stop orders trigger if touched by bar high/low,
- spread is applied first,
- slippage is applied after spread,
- fee is calculated on final notional.

Buy orders become more expensive under spread/slippage. Sell orders receive a worse price.

## 9. Portfolio and Cash Logic

The portfolio is in `engine/core/portfolio.py`.

It tracks:

- cash,
- per-symbol positions,
- per-symbol last prices,
- total market value,
- total equity.

Default behavior is cash-only:

- buys cannot push cash below zero,
- oversized buy orders are reduced to the affordable quantity,
- shorting is disabled unless `allow_short: true`,
- long-only sell orders are capped to current inventory.

This is important. The engine is currently designed for cash-feasible strategy validation first, not leveraged/margin simulation by default.

## 10. Risk Controls

Risk controls are spread across `EngineConfig`, `engine/risk/risk_manager.py`, and engine logic.

Implemented controls:

- `max_abs_weight`: clamps strategy target weights symmetrically.
- `max_abs_exposure`: caps exposure before sizing.
- `max_turnover_qty`: limits position quantity change per bar.
- `max_notional`: caps absolute notional exposure per asset.
- `allow_short`: enables or disables short positions.
- `borrow_rate_bps`: accrues financing for shorts when enabled.
- `stop_loss_mode`: `pct` or `notional`.
- `stop_loss_value`: threshold for stop-loss.
- `stop_cooldown_bars`: keeps a symbol flat after forced liquidation.
- `max_trades_per_day`: caps executed fills by day.
- `trade_cap_side`: applies the daily cap to `buy`, `sell`, or `both`.

Forced stop-loss exits bypass daily trade caps, which is the right safety behavior.

## 11. Accounting System

Accounting is handled by `engine/accounting/ledger.py`.

The ledger is intentionally separate from execution and portfolio state. The engine pushes fills and marks into it.

It tracks:

- per-symbol quantity,
- weighted-average cost,
- realized PnL,
- unrealized PnL,
- total PnL,
- fees paid,
- financing paid,
- journal entries,
- portfolio snapshots,
- trade attribution.

The accounting system supports:

- long positions,
- short positions,
- partial closes,
- direction flips,
- weighted average cost basis,
- borrow cost accrual for short exposure.

This is one of the more mature parts of the project and points toward auditability.

## 12. Strategy Catalog

Strategies live in `strategies/`.

### Moving Average

File: `strategies/moving_average.py`

Parameters:

- `fast_window`
- `slow_window`

Logic:

- if fast SMA is above slow SMA, target `+1.0`;
- otherwise target `-1.0`;
- in long-only mode, negative target is clamped to `0.0`.

Aliases:

- `moving_average`
- `ma`
- `ma_cross`

### Momentum

File: `strategies/momentum.py`

Parameter:

- `lookback`

Logic:

- computes return over lookback window;
- positive return targets `+1.0`;
- negative return targets `-1.0`.

Aliases:

- `momentum`
- `mom`

### Mean Reversion

File: `strategies/mean_reversion.py`

Parameters:

- `window`
- `z_threshold`

Logic:

- calculates z-score of latest price against rolling mean/std;
- high positive z-score targets short;
- high negative z-score targets long;
- otherwise flat.

Aliases:

- `mean_reversion`
- `mr`

### Hull Moving Average

File: `strategies/hull_moving_average.py`

Parameters:

- `fast_window`
- `slow_window`

Logic:

- calculates fast and slow HMA;
- fast above slow targets long;
- otherwise short.

Aliases:

- `hull_moving_average`
- `hma`

### KAMA

File: `strategies/kama.py`

Parameters:

- `er_window`
- `fast_period`
- `slow_period`

Logic:

- calculates Kaufman's Adaptive Moving Average;
- price above KAMA targets long;
- otherwise short.

Aliases:

- `kama`
- `adaptive_ma`

### ZLEMA

File: `strategies/zlema.py`

Parameters:

- `fast_window`
- `slow_window`

Logic:

- calculates zero-lag EMAs;
- fast above slow targets long;
- otherwise short.

Aliases:

- `zlema`
- `zero_lag_ema`

## 13. Strategy Factory

Strategies are created through `strategies/factory.py`.

This centralizes strategy selection:

```python
strategy = build_strategy(strategy_cfg.get("name", "moving_average"), strategy_cfg)
```

This is the right design for config-driven experiments because the runner does not need to know each strategy class directly.

## 14. Data Loading

Data loaders live in `data/loaders/`.

### CSV Loader

File: `data/loaders/csv_loader.py`

Expected columns:

- `date` or `Date`
- `open` or `Open`
- `high` or `High`
- `low` or `Low`
- `close` or `Close`
- `volume` or `Volume`

The loader emits `MarketEvent` objects.

### yfinance Loader

File: `data/loaders/yfinance_loader.py`

Uses:

```python
yfinance.download(...)
```

Parameters:

- `symbol`
- `period`
- `interval`
- `auto_adjust`
- `prepost`
- `progress`

It formats timestamps as:

```text
YYYY-MM-DD HH:MM
```

This timestamp format is important for intraday data and daily trade caps.

## 15. Analytics

Analytics live in `analytics/`.

### Core Metrics

Implemented in:

- `performance.py`
- `drawdown.py`
- `risk_metrics.py`

Metrics:

- equity returns,
- CAGR,
- Sharpe ratio,
- drawdown series,
- max drawdown,
- Calmar ratio.

### Extended Metrics

Implemented in `analytics/extended.py`.

Metrics include:

- number of round-trip trades,
- win rate,
- turnover,
- rolling Sharpe mean,
- rolling Sharpe last,
- max drawdown duration,
- average drawdown duration,
- average absolute exposure,
- peak absolute exposure,
- benchmark CAGR,
- active CAGR,
- tracking error,
- information ratio.

### Tearsheet API

Implemented in `analytics/tearsheet.py`.

Two public functions:

```python
make_tearsheet(equity_curve)
make_tearsheet_with_details(...)
```

`make_tearsheet()` keeps backward-compatible core metrics.  
`make_tearsheet_with_details()` is the richer research function.

## 16. Experiment Scripts

### `experiments/run_backtest.py`

This is the main configured runner.

It:

1. loads `configs/default.yaml`,
2. builds `EngineConfig`,
3. builds a strategy from the factory,
4. loads bars,
5. optionally runs a buy-and-hold benchmark,
6. runs the backtest,
7. computes metrics,
8. writes artifacts,
9. prints metrics and artifact path.

### `experiments/run_grid_search.py`

Runs a small parameter sweep on synthetic data.

Current sweep:

- fast windows: `5`, `10`, `15`
- slow windows: `20`, `30`, `50`

Ranks by Sharpe ratio.

This is useful for quick intuition, not final validation.

### `experiments/run_walkforward.py`

Runs walk-forward validation on synthetic regime-changing data.

Workflow:

1. train on one window,
2. select best MA parameters by Sharpe,
3. test on the next window,
4. roll forward.

This is a first step toward reducing overfitting.

### `experiments/run_cost_sensitivity.py`

Sweeps execution-cost assumptions:

- fee bps,
- slippage bps,
- spread bps.

It reports how performance changes under more expensive trading assumptions.

This is important because many trading strategies look good before costs and disappear after costs.

## 17. Artifact Outputs

`run_backtest.py` writes artifacts under:

```text
artifacts/runs/<run_id>_<strategy_name>/
```

Files:

- `config.snapshot.json`
- `metrics.summary.json`
- `run_meta.json`
- `equity_curve.csv`
- `fills.csv`
- `positions.csv`
- `positions_by_symbol.csv`
- `portfolio_history.csv`
- `ledger_journal.csv`
- `trade_attribution.csv`

The `run_meta.json` includes:

- run id,
- creation timestamp,
- git commit,
- Python version.

This gives each experiment a reproducible record.

## 18. Test Suite

Tests live under `tests/`.

Coverage areas:

- accounting ledger,
- config loader,
- execution model,
- portfolio updates,
- metrics,
- yfinance loader,
- strategy factory,
- newer MA strategy variants,
- configured data loading,
- Phase 3 realism controls,
- Phase 4 analytics,
- Phase 5 multi-asset behavior.

Notable behavior verified by tests:

- multi-asset rebalancing happens per timestamp,
- missing target symbols flatten existing positions,
- cash-only mode prevents negative cash,
- long-only mode blocks short positions,
- sell orders are capped to inventory when shorts are disabled,
- stop-loss exits work,
- stop-loss cooldown works,
- daily trade caps work,
- forced safety exits bypass trade caps,
- run outputs include detailed fill/position/cash series,
- extended analytics produce trade and drawdown metrics.

I could not run the suite during this documentation pass because the active local Python environment did not have `pytest` installed.

## 19. Important Design Decisions

### Strategies Output Weights, Not Orders

Strategies do not place orders directly. They express desired portfolio weights.

This is a strong design because it separates:

- signal logic,
- sizing,
- risk controls,
- execution simulation,
- portfolio accounting.

### Engine Is Multi-Asset by Timestamp

Bars are grouped into snapshots, allowing strategies to compare assets at the same timestamp.

This supports future strategies like:

- top-N momentum,
- sector rotation,
- equal-risk baskets,
- pairs trading,
- portfolio rebalancing,
- benchmark-relative allocation.

### Default Is Conservative

The default path is:

- cash-only,
- long-only,
- no negative cash,
- no accidental short selling.

This prevents unrealistic results for common beginner mistakes.

### Accounting Is Separate

The accounting ledger is separate from portfolio execution. This makes it easier to audit and extend.

## 20. Current Limitations and Risks

### 20.1 Equity Curve Length Can Be Confusing

The README notes that `equity_curve` can be longer than `timestamps` in multi-asset runs because equity is appended on each mark-to-market call, and mark-to-market can happen multiple times per timestamp.

This is expected by the current implementation, but it can make analytics alignment tricky.

Potential improvement:

- create a canonical `basket_equity_curve` with exactly one point per timestamp.

### 20.2 Strategy Weights Are Not Portfolio-Normalized Across Assets

If a strategy returns `1.0` for each of three symbols, the intended gross exposure could exceed 100%. The engine has cash-only protection and `max_abs_weight`, but the target-weight semantics may surprise users.

Potential improvement:

- add a gross exposure normalizer,
- add explicit portfolio-level max gross exposure,
- document whether weights are per-symbol or portfolio-total.

### 20.3 Benchmark Alignment Is Basic

Benchmark comparison aligns curves by shortest length, not by timestamp.

Potential improvement:

- align strategy and benchmark on timestamps.

### 20.4 Trade List Is Basic

`trade_list_from_fills()` handles simple round trips, but richer multi-asset partial exits and direction flips may need more robust trade reconstruction.

Potential improvement:

- use ledger attribution as the canonical trade-level source.

### 20.5 Config Inheritance Is Not Implemented

`configs/experiments/ma_cross.yaml` contains:

```yaml
inherits: ../default.yaml
```

But `load_yaml()` only loads a YAML file; it does not appear to resolve inheritance.

Potential improvement:

- implement recursive config inheritance and deep merge.

### 20.6 Notebook and Script Drift

The notebooks likely contain important research context, but the executable source is now the source of truth.

Potential improvement:

- add a `docs/` folder that explains which notebooks are historical and which are current.

### 20.7 Missing CLI

The main runner always uses `configs/default.yaml`.

Potential improvement:

```bash
python -m experiments.run_backtest --config configs/experiments/ma_cross.yaml
```

### 20.8 No Persistent Run Index

Runs are saved into timestamped folders, but there is no summary index.

Potential improvement:

- write `artifacts/runs/index.csv`,
- include key metrics per run,
- make experiment comparison easier.

## 21. Suggested Roadmap

### Short-Term

- Add CLI arguments to `run_backtest.py`.
- Implement config inheritance for experiment YAMLs.
- Add one equity point per timestamp for analytics alignment.
- Update README with a clearer "current architecture" section.
- Add examples for multi-symbol strategies.
- Install and run tests in CI.

### Medium-Term

- Add portfolio-level gross/net exposure limits.
- Add timestamp-aware benchmark alignment.
- Add richer trade attribution reports.
- Add parameter search using real configured data, not only synthetic bars.
- Add run comparison utilities.
- Add plotting scripts for equity, drawdown, positions, and fills.

### Longer-Term

- Add a formal strategy registry.
- Add a CLI or small dashboard for experiments.
- Add train/test split and walk-forward tools using real data.
- Add portfolio construction models such as equal weight, inverse volatility, and top-N ranking.
- Add risk parity or volatility targeting.
- Add transaction-cost model variants.
- Add support for data caching.

## 22. How to Add a New Strategy

1. Create a file in `strategies/`, for example:

```python
from strategies.base_strategy import BaseStrategy


class MyStrategy(BaseStrategy):
    def on_bars(self, bars_by_symbol):
        targets = {}
        for symbol, bar in bars_by_symbol.items():
            targets[symbol] = 1.0
        return targets
```

2. Add it to `strategies/factory.py`.

3. Configure it in YAML:

```yaml
strategy:
  name: my_strategy
  my_param: 123
```

4. Add tests under `tests/`.

5. Run:

```bash
python -m experiments.run_backtest
```

## 23. How to Add a New Data Source

1. Add a loader under `data/loaders/`.
2. Return a list of `MarketEvent` objects.
3. Update `experiments/run_backtest.py::load_bars`.
4. Add config keys under `data:`.
5. Add tests for loader behavior.

## 24. How to Interpret Results

Start with:

- CAGR: annualized growth.
- Sharpe: risk-adjusted return.
- MaxDrawdown: largest peak-to-trough decline.
- Calmar: CAGR divided by absolute max drawdown.

Then check:

- NumTrades: whether strategy trades too much or too little.
- Turnover: how expensive the strategy may be in practice.
- WinRate: useful, but not sufficient by itself.
- RollingSharpeMean and RollingSharpeLast: whether performance is stable.
- Drawdown duration: how long the strategy spends underwater.
- Exposure metrics: how much capital is actually at risk.
- Benchmark metrics: whether the strategy beats passive exposure.

For realistic interpretation, always compare performance before and after costs using `run_cost_sensitivity.py`.

## 25. Project Identity

A clearer name for the project might be:

- `quant-research-lab`
- `multi-asset-backtest-engine`
- `systematic-strategy-sandbox`
- `portfolio-backtesting-lab`

The current name, `backtesting`, is accurate but undersells the project. The project is moving toward a configurable research platform.

## 26. Final Takeaway

Your original vision seems to have been:

> Build a modular research environment for testing trading strategies, starting from notebooks but growing into a reusable backtesting engine with realistic execution, risk controls, multi-asset support, analytics, and reproducible experiment artifacts.

The current codebase is already well along that path. The next best step is not to rewrite it, but to clarify the interfaces, make runs easier to configure from the command line, normalize multi-asset analytics alignment, and add a higher-level experiment comparison workflow.
