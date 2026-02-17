from typing import Dict, Any
from broker_interface import Order, Fill

class PaperBroker:
    def __init__(self, starting_balance: float = 50.0):
        self.balance = starting_balance
        self.positions = {}

    def get_balance(self) -> float:
        return self.balance

    def get_markets(self) -> list[Dict[str, Any]]:
        return [
            {"market_id": "DUMMY1", "yes_price": 0.35, "no_price": 0.65},
        ]

    def place_order(self, order: Order) -> Fill:
        cost = order.price * order.size
        if cost > self.balance:
            raise RuntimeError("잔고 부족(페이퍼)")
        self.balance -= cost
        self.positions[order.market_id] = self.positions.get(order.market_id, 0.0) + order.size
        return Fill(order=order, filled_size=order.size, avg_price=order.price)

    def get_positions(self) -> Dict[str, Any]:
        return {"positions": dict(self.positions), "balance": self.balance}
