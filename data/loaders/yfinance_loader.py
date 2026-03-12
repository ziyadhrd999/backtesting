from __future__ import annotations

from typing import Any

from engine.core.event import MarketEvent


def _series(dataframe: Any, name: str, symbol: str):
    series = dataframe[name]
    if hasattr(series, "columns") and symbol in getattr(series, "columns", []):
        return series[symbol]
    return series


def load_yfinance(
    symbol: str,
    period: str = "2y",
    interval: str = "1d",
    auto_adjust: bool = True,
    prepost: bool = True,
    progress: bool = False,
) -> list[MarketEvent]:
    import yfinance as yf  # type: ignore

    market = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=auto_adjust,
        progress=progress,
        prepost=prepost,
    )

    if market is None or market.empty:
        return []

    open_s = _series(market, "Open", symbol)
    high_s = _series(market, "High", symbol)
    low_s = _series(market, "Low", symbol)
    close_s = _series(market, "Close", symbol)
    vol_s = _series(market, "Volume", symbol)

    bars: list[MarketEvent] = []
    for idx in close_s.dropna().index:
        bars.append(
            MarketEvent(
                timestamp=idx.strftime("%Y-%m-%d %H:%M"),
                symbol=symbol,
                open=float(open_s.loc[idx]),
                high=float(high_s.loc[idx]),
                low=float(low_s.loc[idx]),
                close=float(close_s.loc[idx]),
                volume=float(vol_s.loc[idx]),
            )
        )
    return bars
