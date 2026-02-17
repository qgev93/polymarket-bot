from dataclasses import dataclass
from typing import Dict, Any, Optional
from broker_interface import Order

@dataclass
class Decision:
    order: Optional[Order]
    reason: str

def decide(market: Dict[str, Any]) -> Decision:
    yes_price = float(market["yes_price"])
    market_id = market["market_id"]

    if yes_price <= 0.40:
        return Decision(
            order=Order(
                market_id=market_id,
                side="BUY_YES",
                price=yes_price,
                size=5.0
            ),
            reason=f"yes_price={yes_price} <= 0.40"
        )

    return Decision(order=None, reason="no edge")
