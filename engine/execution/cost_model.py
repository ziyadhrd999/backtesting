def linear_cost(notional: float, fee_bps: float) -> float:
    return abs(notional) * fee_bps / 10_000
