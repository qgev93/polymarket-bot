from dataclasses import dataclass
from broker_interface import Order
from config import MAX_BET_USD

@dataclass
class RiskResult:
    ok: bool
    adjusted_order: Order | None
    reason: str

def apply_risk(order: Order, balance: float) -> RiskResult:
    cost = order.price * order.size

    if cost > MAX_BET_USD:
        new_size = MAX_BET_USD / order.price
        order = Order(
            market_id=order.market_id,
            side=order.side,
            price=order.price,
            size=new_size
        )
        cost = order.price * order.size

    if cost > balance:
        return RiskResult(False, None, "balance too low")

    return RiskResult(True, order, "ok")
