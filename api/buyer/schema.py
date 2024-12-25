from pydantic import BaseModel
from datetime import datetime


class BuyerBase(BaseModel):
    id: int


class BuyerCreate(BuyerBase):
    name: str
    date_of_delivery: datetime
    crates_desired: int
    amount: int
    status_of_delivery: str


class BuyerUpdate(BuyerBase):
    date_of_delivery: datetime
    crates_desired: int
    amount: int
    status_of_delivery: str


class Buyer(BaseModel):
    id: int
    name: str
    date_of_delivery: datetime
    crates_desired: int
    amount: int
    status_of_delivery: str


class BuyerOutput(BaseModel):
    id: int
    name: str
    date_of_delivery: datetime
    crates_desired: int
    amount: int
    status_of_delivery: str
    created_at: datetime
    updated_at: datetime