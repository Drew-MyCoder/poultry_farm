from sqlalchemy import Column, String, Integer, Enum, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from base import Base
import enum
from datetime import datetime, timezone
from pydantic import validator



status_option = ['active', 'inactive', 'suspended']


# class Role(enum.Enum):
#     ADMIN = 'admin'
#     FEEDER = 'feeder'
#     COUNTER = 'counter'

role_option = ['admin', 'feeder', 'counter']


status_of_delivery = ["pending", "delivered", "cancelled", "progress"]


class DBUser(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default='feeder')
    username = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False)
    provider = Column(String, default='custom')
    hashed_otp = Column(String, default="")


    def __init__(
        self,
        id: int | None = None,
        username: str | None = None,
        password: str | None = None,
        role: str | None = None,
        email: str | None = None,
        status: str | None = None,
        provider: str = 'custom',
        hashed_otp: str = "",
    ):
        self.id = id
        self.username = username
        self.password = password
        self.role = role
        self.email = email
        self.status = status
        self.provider = provider
        self.hashed_otp = hashed_otp
      

    @validator("status option")
    def validate_status(status, status_option):
        if status not in status_option:
            raise ValueError("Invalid status value")

    
    @validator("role option")
    def validate_role(role, role_option):
        if role not in role_option:
            raise ValueError("Invalid role value")


class DBBlacklistedToken(Base):
    __tablename__ = "blacklisted_tokens"
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String, unique=True, nullable=False)

    def __init__(self, jti: str):
        self.jti = jti

    def __repr__(self) -> str:
        return str(self.jti)

    def __str__(self) -> str:
        return str(self.jti)


class DBReset(Base):
    __tablename__ = "reset_password"
    id = Column(Integer, primary_key=True)
    email = Column(String)
    reset_code = Column(String)
    status = Column(String)
    expired = Column(DateTime)
    hashed_otp = Column(String, default="")

    def __init__(
        self,
        id: int | None = None,
        email: str | None = None,
        reset_code: str | None = None,
        status: str | None = None,
        hashed_otp: str = "",
    ):
        self.id = id
        self.email = email
        self.reset_code = reset_code
        self.status = status
        self.hashed_otp = hashed_otp
    

class DBCoops(Base):
    __tablename__ = "coop"

    id = Column(Integer, primary_key=True, index=True)
    parent_id = Column(Integer, ForeignKey("coop.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, nullable=False)
    total_fowls = Column(Integer, nullable=False, default=0)
    total_dead_fowls = Column(Integer, nullable=False, default=0)
    total_feed = Column(Integer, nullable=False, default=0)
    coop_name = Column(String, index=True)
    egg_count = Column(Integer, default=0)
    collection_date = Column(String, nullable=False)
    crates_collected = Column(Integer, nullable=False, default=0)
    remainder_eggs = Column(Integer, nullable=False, default=0)
    broken_eggs = Column(Integer, nullable=False, default=0)
    notes = Column(String, nullable=False)
    efficiency = Column(Float, nullable=False, default=0)


    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


    def __init__(
        self,
        id: int | None = None,
        parent_id: int | None = None,
        user_id: int | None = None,
        status: str | None = None,
        total_fowls: int | None = None,
        total_dead_fowls: int | None = None,
        total_feed: int | None = None,
        coop_name: str | None = None,
        egg_count: int | None = None,
        collection_date: str | None = None,
        crates_collected: int | None = None,
        remainder_eggs: int | None = None,
        broken_eggs: int | None = None,
        notes: str | None = None,
        efficiency: float | None = None
    ):
        self.id = id
        self.parent_id = parent_id
        self.user_id = user_id
        self.status = status
        self.total_fowls = total_fowls
        self.total_dead_fowls = total_dead_fowls
        self.total_feed = total_feed
        self.coop_name = coop_name
        self.egg_count = egg_count
        self.collection_date = collection_date
        self.crates_collected = crates_collected
        self.remainder_eggs = remainder_eggs
        self.broken_eggs = broken_eggs
        self.notes = notes
        self.efficiency = efficiency


class DBBuyer(Base):
    __tablename__ = "buyer"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    crates_desired = Column(Integer, nullable=False, default=0)
    date_of_delivery = Column(DateTime, nullable=False)
    amount = Column(Integer, nullable=False)
    status_of_delivery = Column(String, default='pending')
    coop_id = Column(Integer, ForeignKey("coop.id"))

    # coop = relationship("Coop", back_populates="buyers")

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    by = Column(String, nullable=False)


    def __init__(
        self,
        id: int | None = None,
        name: str | None = None,
        crates_desired: int | None = None,
        date_of_delivery: str | None = None,
        amount: int | None = None,
        status_of_delivery: str | None = None,
        coop_id: int | None = None,
        by: str | None = None,
    ):
        self.id = id
        self.name = name
        self.crates_desired = crates_desired
        self.date_of_delivery = date_of_delivery
        self.amount = amount
        self.status_of_delivery = status_of_delivery
        self.coop_id = coop_id
        self.by = by


class DBExpenditure(Base):
    __tablename__ = "expenditure"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False)
    reference = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __init__(
        self,
        id: int | None = None,
        amount: int | None = None,
        reference: str | None = None,
        user_id: int | None = None,
    ):
        self.id = id
        self.amount = amount
        self.reference = reference
        self.user_id = user_id
