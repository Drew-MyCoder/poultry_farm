from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date


class BuyerBase(BaseModel):
    id: int


class BuyerCreate(BaseModel):
    name: str
    date_of_delivery: date
    crates_desired: int
    amount: int
    status_of_delivery: str
    by: str
    location_id: int


class BuyerUpdate(BaseModel):
    amount: Optional[int] = None
    crates_desired: Optional[int] = None
    date_of_delivery: Optional[date] = None  # Ensure it's a `date`, not `datetime`
    status_of_delivery: Optional[str] = None

    class Config:
        orm_mode = True


class Buyer(BaseModel):
    id: int
    name: str
    date_of_delivery: datetime
    crates_desired: int
    amount: int
    status_of_delivery: str
    by: str


class BuyerOutput(BaseModel):
    id: int
    name: str
    date_of_delivery: datetime
    crates_desired: int
    amount: int
    status_of_delivery: str
    created_at: datetime
    updated_at: datetime
    by: str