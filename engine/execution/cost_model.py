def linear_cost(notional: float, fee_bps: float) -> float:
    """
    Calculates the transaction fee as a linear trading cost based on the trade's notional value and fee rate in basis points (bps).

    Basis points explanation:
        1 basis point (bps) = 0.01% = 0.0001
        To convert bps to a percentage: bps / 10,000

        10 bps (0.10%)

        100 bps (1.00%)
            
        250 bps (2.50%)
    Example:
        
    If you have a trade with a notional value of $10,000 and a fee of 5 bps:
    
    notional = 10,000
        fee_bps = 5

        fee = 10,000 * (5 / 10,000)
        fee = 5.0

        So the trading fee would be $5.

    Args:
        notional: Total value of the trade (price × quantity).
        fee_bps: Trading fee expressed in basis points.

    Returns:
        The transaction fee for the trade.
    """
    return abs(notional) * fee_bps / 10_000