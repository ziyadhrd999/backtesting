from abc import ABC, abstractmethod

from engine.core.event import MarketEvent


class BaseStrategy(ABC):
    @abstractmethod
    def on_bars(self, bars_by_symbol: dict[str, MarketEvent]) -> dict[str, float]:
        """Return per-symbol target weights in ``[-1, +1]``.

        Args:
            bars_by_symbol: Snapshot of latest bars keyed by symbol.

        Returns:
            Mapping from symbol to target portfolio weight.
        """
