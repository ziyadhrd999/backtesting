def apply_slippage(price: float, slippage_bps: float, side: str) -> float:
    bump = slippage_bps / 10_000
    if side == "BUY":
        return price * (1 + bump)
    return price * (1 - bump)
