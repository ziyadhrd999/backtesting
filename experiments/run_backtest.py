from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from analytics.tearsheet import make_tearsheet
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import MarketEvent
from engine.utils.config import load_yaml
from strategies.factory import build_strategy


def synthetic_bars(n: int = 300) -> list[MarketEvent]:
    bars = []
    price = 100.0
    for i in range(n):
        drift = 0.0008 if i < n // 2 else -0.0002
        shock = ((i % 7) - 3) * 0.001
        price *= 1 + drift + shock
        bars.append(MarketEvent(timestamp=f"t{i}", symbol="SYNTH", close=price))
    return bars


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

    engine = BacktestEngine(engine_cfg)
    equity = engine.run(synthetic_bars(), strategy)
    print(make_tearsheet(equity, annualization=int(cfg["engine"].get("annualization", 252))))
