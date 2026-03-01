import csv

from engine.core.event import MarketEvent


def _num(row: dict, *keys: str, default: float) -> float:
    for key in keys:
        if key in row and row[key] not in {None, ""}:
            return float(row[key])
    return default


def load_csv(path: str, symbol: str) -> list[MarketEvent]:
    bars: list[MarketEvent] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            close = _num(row, "close", "Close", default=0.0)
            bars.append(
                MarketEvent(
                    timestamp=row.get("date") or row.get("Date") or "",
                    symbol=symbol,
                    open=_num(row, "open", "Open", default=close),
                    high=_num(row, "high", "High", default=close),
                    low=_num(row, "low", "Low", default=close),
                    close=close,
                    volume=_num(row, "volume", "Volume", default=0.0),
                )
            )
    return bars
