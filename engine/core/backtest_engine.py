from dataclasses import dataclass

from engine.core.broker import SimBroker
from engine.core.event import MarketEvent, OrderEvent
from engine.core.portfolio import Portfolio
from engine.risk.position_sizer import target_qty_from_weight
from engine.risk.risk_manager import clamp_weight


@dataclass
class EngineConfig:
    """Configuration parameters controlling initial capital and execution frictions."""

    initial_cash: float = 100_000.0
    fee_bps: float = 1.0
    slippage_bps: float = 2.0
    spread_bps: float = 1.0


class BacktestEngine:
    """Minimal event-driven engine for running backtests on a single asset."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.portfolio = Portfolio(initial_cash=config.initial_cash)
        self.broker = SimBroker(
            fee_bps=config.fee_bps,
            slippage_bps=config.slippage_bps,
            spread_bps=config.spread_bps,
        )

    def run(self, bars: list[MarketEvent], strategy) -> list[float]:
        for bar in bars:
            self.portfolio.mark_to_market(price=bar.close)
            target_weight = clamp_weight(strategy.on_bar(bar), max_abs_weight=1.0)
            target_qty = target_qty_from_weight(
                equity=self.portfolio.state.equity,
                price=bar.close,
                target_weight=target_weight,
            )
            delta = target_qty - self.portfolio.state.position_qty
            if abs(delta) < 1e-9:
                continue

            side = "BUY" if delta > 0 else "SELL"
            order = OrderEvent(
                timestamp=bar.timestamp,
                symbol=bar.symbol,
                side=side,
                quantity=abs(delta),
                order_type="MARKET",
            )
            fill = self.broker.execute(order=order, bar=bar)
            if fill is None:
                continue

            self.portfolio.on_fill(
                side=fill.side,
                quantity=fill.quantity,
                fill_price=fill.fill_price,
                fee=fill.fee,
            )
            self.portfolio.mark_to_market(price=bar.close)

        return self.portfolio.equity_curve
