from pydantic import BaseModel
from datetime import datetime


class ExpenditureBase(BaseModel):
    user_id: int


class ExpenditureCreate(ExpenditureBase):
    # id: int
    amount: int
    reference: str


class ExpenditureUpdate(ExpenditureBase):
    amount: int
    reference: str


class Expenditure(BaseModel):
    id: int
    user_id: int
    amount: int
    reference: str


class ExpenditureOutput(BaseModel):
    id: int
    user_id: int
    amount: int
    reference: str
    created_at: datetime
    updated_at: datetime