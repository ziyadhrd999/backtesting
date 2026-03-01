from analytics.performance import sharpe_ratio
from engine.core.backtest_engine import BacktestEngine, EngineConfig
from engine.core.event import MarketEvent
from strategies.moving_average import MovingAverageStrategy


def synthetic_bars(n: int = 600) -> list[MarketEvent]:
    bars = []
    price = 100.0
    for i in range(n):
        regime = 0.001 if (i // 150) % 2 == 0 else -0.0004
        shock = ((i % 9) - 4) * 0.0008
        price *= 1 + regime + shock
        bars.append(MarketEvent(timestamp=f"t{i}", symbol="SYNTH", close=price))
    return bars


if __name__ == "__main__":
    bars = synthetic_bars()
    train_size, test_size = 200, 100
    start = 0
    while start + train_size + test_size <= len(bars):
        train = bars[start : start + train_size]
        test = bars[start + train_size : start + train_size + test_size]

        best = None
        for fast in [5, 10, 15]:
            for slow in [20, 30, 50]:
                if fast >= slow:
                    continue
                engine = BacktestEngine(EngineConfig())
                strat = MovingAverageStrategy(fast_window=fast, slow_window=slow)
                score = sharpe_ratio(engine.run(train, strat))
                if best is None or score > best[0]:
                    best = (score, fast, slow)

        engine = BacktestEngine(EngineConfig())
        strat = MovingAverageStrategy(fast_window=best[1], slow_window=best[2])
        test_sharpe = sharpe_ratio(engine.run(test, strat))
        print({"window_start": start, "fast": best[1], "slow": best[2], "test_sharpe": test_sharpe})

        start += test_size
