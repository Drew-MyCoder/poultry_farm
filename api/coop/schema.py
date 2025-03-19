from pydantic import BaseModel
from datetime import datetime


class CoopBase(BaseModel):
    user_id: int


class CoopCreate(BaseModel):
    status: str
    total_dead_fowls: int
    total_feed: int
    total_fowls: int
    coop_name: str
    user_id: int
    crates_collected: int
    remainder_eggs: int
    broken_eggs: int
    notes: str
    collection_date: datetime
    efficiency: float
    egg_count: int


class CoopStatus(BaseModel):
    status: str


class CoopEgg(BaseModel):
    egg_count: int


class CoopUpdate(BaseModel):
    total_fowls: int
    total_dead_fowls: int
    total_feed: int
    coop_name: str
    egg_count: int
    crates_collected: int
    remainder_eggs: int
    broken_eggs: int
    notes: str
    efficiency: float


class Coop(BaseModel):
    id: int
    status: str
    coop_name: str
    total_dead_fowls: int
    total_fowls: int
    total_feed: int
    user_id: int
    


class CoopOutput(BaseModel):
    id: int
    status: str
    total_dead_fowls: int
    total_fowls: int
    coop_name: str
    total_feed: int
    created_at: datetime
    updated_at: datetime
    egg_count: int
    efficiency: float
    collection_date: datetime
    broken_eggs: int
    notes: str