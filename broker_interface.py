from dataclasses import dataclass
from typing import Protocol, Dict, Any, Optional

@dataclass
class Order:
    market_id: str
    side: str
    price: float
    size: float

@dataclass
class Fill:
    order: Order
    filled_size: float
    avg_price: float

class Broker(Protocol):
    def get_balance(self) -> float: ...
    def get_markets(self) -> list[Dict[str, Any]]: ...
    def place_order(self, order: Order) -> Fill: ...
    def get_positions(self) -> Dict[str, Any]: ...
