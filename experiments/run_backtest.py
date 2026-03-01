from pathlib import Path

from analytics.tearsheet import make_tearsheet
from data.loaders import load_csv, load_yfinance
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.utils.config import load_yaml
from strategies.factory import build_strategy


def load_bars(cfg: dict) -> list:
    data_cfg = cfg.get("data", {})
    source = str(data_cfg.get("source", "yfinance")).lower().strip()

    if source == "yfinance":
        return load_yfinance(
            symbol=str(data_cfg.get("symbol", "NVDA")),
            period=str(data_cfg.get("period", "2y")),
            interval=str(data_cfg.get("interval", "1d")),
            auto_adjust=bool(data_cfg.get("auto_adjust", True)),
        )

    if source == "csv":
        csv_path = Path(data_cfg["path"])
        return load_csv(path=str(csv_path), symbol=str(data_cfg.get("symbol", "CSV")))

    raise ValueError(f"Unsupported data source: {source}")


if __name__ == "__main__":
    config_path = Path(__file__).resolve().parents[1] / "configs" / "default.yaml"
    cfg = load_yaml(config_path)

    engine_cfg = EngineConfig(
        initial_cash=float(cfg["engine"]["initial_cash"]),
        fee_bps=float(cfg["engine"]["fee_bps"]),
        slippage_bps=float(cfg["engine"]["slippage_bps"]),
    )

    strategy_cfg = cfg.get("strategy", {})
    strategy = build_strategy(strategy_cfg.get("name", "moving_average"), strategy_cfg)

    bars = load_bars(cfg)
    if not bars:
        raise RuntimeError("No bars were loaded. Check your data config.")

    engine = BacktestEngine(engine_cfg)
    equity = engine.run(bars, strategy)
    print(make_tearsheet(equity, annualization=int(cfg["engine"].get("annualization", 252))))
