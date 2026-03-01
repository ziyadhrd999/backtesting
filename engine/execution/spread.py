def apply_spread(price: float, spread_bps: float, side: str) -> float:
    """Apply half-spread around a mid price (buys pay ask, sells hit bid)."""
    half = (spread_bps / 10_000) / 2
    if side == "BUY":
        return price * (1 + half)
    return price * (1 - half)
