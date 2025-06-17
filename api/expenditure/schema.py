from pydantic import BaseModel
from datetime import datetime


class ExpenditureBase(BaseModel):
    user_id: int


class ExpenditureCreate(ExpenditureBase):
    # id: int
    amount: int
    reference: str
    category: str
    status: str
    approved_by: str
    payment_method: str
    location_id: int


class ExpenditureUpdate(BaseModel):
    payment_method: str
    reference: str
    category: str
    status: str
    approved_by: str


class Expenditure(BaseModel):
    id: int
    user_id: int
    amount: int
    reference: str
    category: str
    status: str
    approved_by: str
    payment_method: str


class ExpenditureOutput(BaseModel):
    id: int
    user_id: int
    amount: int
    reference: str
    created_at: datetime
    updated_at: datetime
    category: str
    status: str
    approved_by: str
    payment_method: str