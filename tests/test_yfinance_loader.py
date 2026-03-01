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

    def dropna(self):
        return self

    def items(self):
        return iter(self._values)


class FakeFrame:
    empty = False

    def __getitem__(self, key: str):
        if key != "Close":
            raise KeyError(key)
        return FakeSeries(
            [
                (FakeIndexItem("2024-01-01"), 10.0),
                (FakeIndexItem("2024-01-02"), 11.0),
                (FakeIndexItem("2024-01-03"), 12.5),
            ]
        )


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
    assert bars[-1].close == 12.5
