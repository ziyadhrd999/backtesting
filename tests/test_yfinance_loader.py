import sys

from data.loaders.yfinance_loader import load_yfinance


class FakeIndexItem:
    def __init__(self, date_str: str) -> None:
        self._date_str = date_str

    def strftime(self, _: str) -> str:
        return self._date_str


class FakeSeries:
    def __init__(self, values):
        self._values = values
        self.index = [k for k, _ in values]

    def dropna(self):
        return self

    @property
    def loc(self):
        return self

    def __getitem__(self, key):
        for k, v in self._values:
            if k is key:
                return v
        raise KeyError(key)


class FakeFrame:
    empty = False

    def __init__(self) -> None:
        self._base = [
            (FakeIndexItem("2024-01-01"), 10.0),
            (FakeIndexItem("2024-01-02"), 11.0),
            (FakeIndexItem("2024-01-03"), 12.5),
        ]

    def __getitem__(self, key: str):
        if key == "Open":
            return FakeSeries(self._base)
        if key == "High":
            return FakeSeries([(d, v + 1.0) for d, v in self._base])
        if key == "Low":
            return FakeSeries([(d, v - 1.0) for d, v in self._base])
        if key == "Close":
            return FakeSeries(self._base)
        if key == "Volume":
            return FakeSeries([(d, 1000.0) for d, _ in self._base])
        raise KeyError(key)


class FakeYFinanceModule:
    @staticmethod
    def download(*args, **kwargs):
        return FakeFrame()


def test_load_yfinance_maps_to_market_events(monkeypatch):
    monkeypatch.setitem(sys.modules, "yfinance", FakeYFinanceModule())

    bars = load_yfinance(symbol="NVDA", period="1mo", interval="1d")

    assert len(bars) == 3
    assert bars[0].symbol == "NVDA"
    assert bars[0].timestamp == "2024-01-01"
    assert bars[0].open == 10.0
    assert bars[0].high == 11.0
    assert bars[0].low == 9.0
    assert bars[-1].close == 12.5
    assert bars[-1].volume == 1000.0
