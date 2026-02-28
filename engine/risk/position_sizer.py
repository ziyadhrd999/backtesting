def target_qty_from_weight(equity: float, price: float, target_weight: float) -> float:
    if price <= 0:
        return 0.0
    return (equity * target_weight) / price
