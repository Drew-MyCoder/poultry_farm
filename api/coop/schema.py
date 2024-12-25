from pydantic import BaseModel
from datetime import datetime


class CoopBase(BaseModel):
    user_id: int


class CoopCreate(CoopBase):
    pass


class CoopStatus(BaseModel):
    status: str


class CoopEgg(BaseModel):
    egg_count: int


class CoopUpdate(BaseModel):
    total_fowls: int
    total_dead_fowls: int
    total_feed: int
    coop_name: str


class Coop(CoopBase):
    id: int
    status: str
    coop_name: str
    total_dead_fowls: int
    total_fowls: int
    # total_old_fowls: int
    total_feed: int


class CoopOutput(CoopBase):
    id: int
    status: str
    total_dead_fowls: int
    total_fowls: int
    coop_name: str
    # total_old_fowls: int
    total_feed: int
    created_at: datetime
    update_feed: datetime
    


