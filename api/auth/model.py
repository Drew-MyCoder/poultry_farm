from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from base import Base
from datetime import datetime, timezone
from pydantic import validator

status_option = ['active', 'inactive', 'suspended']
role_option = ['admin', 'feeder', 'manager']
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
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    
    # Fixed relationship with explicit foreign_keys
    location = relationship("DBLocation", foreign_keys=[location_id], back_populates="users")

    @hybrid_property
    def location_name(self):
        """"Get the location name from the related location"""
        return self.location.name if self.location else None

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


class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True, nullable=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    attempt_time = Column(DateTime, default=datetime.utcnow)
    success = Column(Boolean, default=False)
    failure_reason = Column(String, nullable=True)
    

class AccountLockout(Base):
    __tablename__ = "account_lockouts"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    locked_at = Column(DateTime, default=datetime.utcnow)
    unlock_at = Column(DateTime, nullable=False)
    failed_attempts = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)


class DBLocation(Base):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    address = Column(String)
    region = Column(String)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default='active')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Fixed relationships with explicit foreign_keys
    coops = relationship("DBCoops", back_populates="location")
    manager = relationship("DBUser", foreign_keys=[manager_id], post_update=True)
    users = relationship("DBUser", foreign_keys="DBUser.location_id", back_populates="location")
    buyers = relationship("DBBuyer", back_populates="location")
    expenditures = relationship("DBExpenditure", back_populates="location")


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
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    
    # Fixed relationships
    location = relationship("DBLocation", back_populates="coops")
    user = relationship("DBUser", foreign_keys=[user_id])
    # buyers = relationship("DBBuyer", back_populates="coop")  # Added relationship for buyers

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
        efficiency: float | None = None,
        location_id: int | None = None,
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
        self.location_id = location_id


class DBBuyer(Base):
    __tablename__ = "buyer"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    crates_desired = Column(Integer, nullable=False, default=0)
    date_of_delivery = Column(DateTime, nullable=False)
    amount = Column(Integer, nullable=False)
    status_of_delivery = Column(String, default='pending')
    coop_id = Column(Integer, ForeignKey("coop.id"))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)

    # Fixed relationship
    # coop = relationship("DBCoops", back_populates="buyers")
    location = relationship("DBLocation", back_populates="buyers")

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
        location_id: int | None = None,
    ):
        self.id = id
        self.name = name
        self.crates_desired = crates_desired
        self.date_of_delivery = date_of_delivery
        self.amount = amount
        self.status_of_delivery = status_of_delivery
        self.coop_id = coop_id
        self.by = by
        self.location_id = location_id 


class DBExpenditure(Base):
    __tablename__ = "expenditure"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Integer, nullable=False)
    reference = Column(String, nullable=False) #reference is description on front end
    category = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)
    status = Column(String, nullable=False)
    approved_by = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Added relationship
    user = relationship("DBUser", foreign_keys=[user_id])
    location = relationship("DBLocation", back_populates="expenditures")

    def __init__(
        self,
        id: int | None = None,
        amount: int | None = None,
        reference: str | None = None,
        user_id: int | None = None,
        location_id: int | None = None,
        category: str | None = None,
        payment_method: str | None = None,
        status: str | None = None,
        approved_by: str | None = None,
    ):
        self.id = id
        self.amount = amount
        self.reference = reference
        self.user_id = user_id
        self.location_id = location_id
        self.category = category
        self.payment_method = payment_method
        self.status = status
        self.approved_by = approved_by