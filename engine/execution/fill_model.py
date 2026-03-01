from engine.execution.cost_model import linear_cost
from engine.execution.slippage import apply_slippage
from engine.execution.spread import apply_spread


def simulate_fill(
    price: float,
    quantity: float,
    side: str,
    fee_bps: float,
    slippage_bps: float,
    spread_bps: float = 0.0,
) -> tuple[float, float]:
    priced = apply_spread(price=price, spread_bps=spread_bps, side=side)
    fill_price = apply_slippage(price=priced, slippage_bps=slippage_bps, side=side)
    notional = fill_price * quantity
    fee = linear_cost(notional=notional, fee_bps=fee_bps)
    return fill_price, fee
