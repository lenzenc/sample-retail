from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int 
    per_page: int
    total_pages: int

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    FULFILLED = "FULFILLED"

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    barcode: str
    price: float
    is_active: bool = True

class ItemCreate(ItemBase):
    pass

class Item(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime

class OrderItemBase(BaseModel):
    item_id: int
    quantity: int = 1
    unit_price: float
    subtotal: float

class OrderCreate(BaseModel):
    customer_id: int
    picked_key_id: Optional[int] = None
    order_number: str
    order_items: List[OrderItemBase]

class OrderItem(OrderItemBase):
    order_id: int
    created_at: datetime
    updated_at: datetime

class Order(BaseModel):
    id: int
    customer_id: int
    picked_key_id: Optional[int]
    order_number: str
    total_amount: float
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItem] = []