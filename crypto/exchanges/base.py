from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class BalanceSnapshotSchema(BaseModel):
    exchange_name: str
    account: str
    asset: str
    free_snapshot: Decimal
    locked_snapshot: Decimal
    snapshot_time: datetime


class BalanceSchema(BaseModel):
    asset: str
    account: str  # spot, margin, futures, earn, etc.
    free: Decimal
    locked: Decimal
    raw: dict | list | None = None


class TransactionSchema(BaseModel):
    tx_id: str
    asset: str
    account: str
    amount: Decimal
    tx_type: str
    timestamp: datetime


class OrderSchema(BaseModel):
    order_id: str
    symbol: str
    side: str
    order_type: str
    price: Decimal
    quantity: Decimal
    status: str
    created_at: datetime


class CreateOrderSchema(BaseModel):
    symbol: str
    side: str
    order_type: str
    price: Decimal | None = None
    quantity: Decimal


class AbstractExchange(ABC):
    @abstractmethod
    async def fetch_balances(self) -> list[BalanceSchema]:
        ...
