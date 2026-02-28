from engine.execution.cost_model import linear_cost
from engine.execution.slippage import apply_slippage


def simulate_fill(price: float, quantity: float, side: str, fee_bps: float, slippage_bps: float) -> tuple[float, float]:
    fill_price = apply_slippage(price=price, slippage_bps=slippage_bps, side=side)
    notional = fill_price * quantity
    fee = linear_cost(notional=notional, fee_bps=fee_bps)
    return fill_price, fee
