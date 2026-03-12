from engine.core.event import MarketEvent
from experiments.run_backtest import _symbols_from_data_cfg, load_bars


def _mk_bar(symbol: str, ts: str, close: float) -> MarketEvent:
    return MarketEvent(timestamp=ts, symbol=symbol, open=close, high=close, low=close, close=close, volume=1000.0)


def test_symbols_from_cfg_supports_symbol_and_symbols() -> None:
    assert _symbols_from_data_cfg({"symbol": "NVDA"}) == ["NVDA"]
    assert _symbols_from_data_cfg({"symbols": ["NVDA", "MSFT"]}) == ["NVDA", "MSFT"]


def test_symbols_from_cfg_applies_universe_controls() -> None:
    cfg = {
        "symbols": ["NVDA", "MSFT", "AAPL", "MSFT"],
        "include_symbols": ["NVDA", "MSFT", "TSLA"],
        "exclude_symbols": ["MSFT"],
        "max_symbols": 2,
    }
    assert _symbols_from_data_cfg(cfg) == ["NVDA"]


def test_load_bars_yfinance_merges_and_sorts_symbols(monkeypatch) -> None:
    def _fake_load_yfinance(symbol: str, period: str, interval: str, auto_adjust: bool):
        return [
            _mk_bar(symbol, "2024-01-02 00:00", 101.0),
            _mk_bar(symbol, "2024-01-01 00:00", 100.0),
        ]

    monkeypatch.setattr("experiments.run_backtest.load_yfinance", _fake_load_yfinance)

    bars = load_bars(
        {
            "source": "yfinance",
            "symbols": ["MSFT", "AAPL"],
            "period": "1mo",
            "interval": "1d",
            "auto_adjust": True,
        }
    )

    assert [bar.timestamp for bar in bars] == [
        "2024-01-01 00:00",
        "2024-01-01 00:00",
        "2024-01-02 00:00",
        "2024-01-02 00:00",
    ]
    assert [bar.symbol for bar in bars] == ["AAPL", "MSFT", "AAPL", "MSFT"]
