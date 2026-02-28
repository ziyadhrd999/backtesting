def apply_slippage(price: float, slippage_bps: float, side: str) -> float:
    """
    Adjusts the trade price to simulate slippage by increasing buy prices and decreasing sell prices based on basis points.
    """
    bump = slippage_bps / 10_000
    if side == "BUY":
        return price * (1 + bump)
    return price * (1 - bump)