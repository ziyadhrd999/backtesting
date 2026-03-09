from strategies.base_strategy import BaseStrategy
from strategies.hull_moving_average import HullMovingAverageStrategy
from strategies.kama import KAMAStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum import MomentumStrategy
from strategies.moving_average import MovingAverageStrategy
from strategies.zlema import ZLEMAStrategy


def build_strategy(name: str, params: dict) -> BaseStrategy:
    key = name.lower().strip()
    if key in {"moving_average", "ma", "ma_cross"}:
        return MovingAverageStrategy(
            fast_window=int(params.get("fast_window", 20)),
            slow_window=int(params.get("slow_window", 100)),
        )
    if key in {"hull_moving_average", "hma"}:
        return HullMovingAverageStrategy(
            fast_window=int(params.get("fast_window", 16)),
            slow_window=int(params.get("slow_window", 64)),
        )
    if key in {"kama", "adaptive_ma"}:
        return KAMAStrategy(
            er_window=int(params.get("er_window", 10)),
            fast_period=int(params.get("fast_period", 2)),
            slow_period=int(params.get("slow_period", 30)),
        )
    if key in {"zlema", "zero_lag_ema"}:
        return ZLEMAStrategy(
            fast_window=int(params.get("fast_window", 20)),
            slow_window=int(params.get("slow_window", 60)),
        )
    if key in {"momentum", "mom"}:
        return MomentumStrategy(lookback=int(params.get("lookback", 30)))
    if key in {"mean_reversion", "mr"}:
        return MeanReversionStrategy(
            window=int(params.get("window", 20)),
            z_threshold=float(params.get("z_threshold", 1.5)),
        )
    raise ValueError(f"Unsupported strategy: {name}")
