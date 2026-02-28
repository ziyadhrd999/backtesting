from abc import ABC, abstractmethod


class BaseStrategy(ABC):
    @abstractmethod
    def on_bar(self, market_event) -> float:
        """Return target portfolio weight in [-1, +1]."""
