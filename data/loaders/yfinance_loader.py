from __future__ import annotations

from typing import Any

from engine.core.event import MarketEvent


def _close_series(dataframe: Any, symbol: str):
    close = dataframe["Close"]
    # yfinance can return a MultiIndex column shape for multi-ticker requests
    if hasattr(close, "columns") and symbol in getattr(close, "columns", []):
        return close[symbol]
    return close


def load_yfinance(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
    auto_adjust: bool = True,
) -> list[MarketEvent]:
    import yfinance as yf  # type: ignore

    market = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=auto_adjust,
        progress=False,
    )

    if market is None or market.empty:
        return []

    close_series = _close_series(market, symbol).dropna()
    return [
        MarketEvent(timestamp=idx.strftime("%Y-%m-%d"), symbol=symbol, close=float(price))
        for idx, price in close_series.items()
    ]
