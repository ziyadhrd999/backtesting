from strategies.base_strategy import BaseStrategy
from strategies.mean_reversion import MeanReversionStrategy
from strategies.momentum import MomentumStrategy
from strategies.moving_average import MovingAverageStrategy


def build_strategy(name: str, params: dict) -> BaseStrategy:
    key = name.lower().strip()
    if key in {"moving_average", "ma", "ma_cross"}:
        return MovingAverageStrategy(
            fast_window=int(params.get("fast_window", 20)),
            slow_window=int(params.get("slow_window", 100)),
        )
    if key in {"momentum", "mom"}:
        return MomentumStrategy(lookback=int(params.get("lookback", 30)))
    if key in {"mean_reversion", "mr"}:
        return MeanReversionStrategy(
            window=int(params.get("window", 20)),
            z_threshold=float(params.get("z_threshold", 1.5)),
        )
    raise ValueError(f"Unsupported strategy: {name}")
