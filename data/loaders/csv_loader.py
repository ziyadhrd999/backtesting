import csv
from engine.core.event import MarketEvent


def load_csv(path: str, symbol: str) -> list[MarketEvent]:
    bars: list[MarketEvent] = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            bars.append(MarketEvent(timestamp=row["date"], symbol=symbol, close=float(row["close"])))
    return bars
