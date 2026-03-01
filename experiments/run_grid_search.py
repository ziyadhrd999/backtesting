from analytics.performance import sharpe_ratio
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import MarketEvent
from strategies.moving_average import MovingAverageStrategy


def synthetic_bars(n: int = 300) -> list[MarketEvent]:
    bars = []
    price = 100.0
    for i in range(n):
        drift = 0.0006 if i < n // 2 else 0.0001
        shock = ((i % 5) - 2) * 0.001
        price *= 1 + drift + shock
        bars.append(MarketEvent(timestamp=f"t{i}", symbol="SYNTH", close=price))
    return bars


if __name__ == "__main__":
    bars = synthetic_bars()
    rows = []
    for fast in [5, 10, 15]:
        for slow in [20, 30, 50]:
            if fast >= slow:
                continue
            engine = BacktestEngine(EngineConfig())
            strategy = MovingAverageStrategy(fast_window=fast, slow_window=slow)
            equity = engine.run(bars, strategy)
            rows.append((fast, slow, sharpe_ratio(equity)))
    rows.sort(key=lambda x: x[2], reverse=True)
    for row in rows:
        print({"fast": row[0], "slow": row[1], "sharpe": row[2]})
