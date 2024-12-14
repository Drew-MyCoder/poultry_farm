from sqlalchemy import Column, String, Integer, Enum, DateTime, MetaData
from database import Base
import enum
from datetime import datetime, timezone
from pydantic import validator



status_option = ['active', 'inactive', 'suspended']


class Role(enum.Enum):
    ADMIN = 'admin'
    FEEDER = 'feeder'
    COUNTER = 'counter'


class DBUser(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(Enum(Role), default=Role.FEEDER)
    username = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    status = Column(String, nullable=False)
    provider = Column(String, default='custom')


    # def __init__(
    #     self,
    #     id: int | None = None,
    #     username: str | None = None,
    #     hashed_password: str | None = None,
    #     role: str | None = None,
    #     email: str | None = None,
    #     status: str | None = None,
    #     provider: str = 'custom',
    # ):
    #     self.id = id
    #     self.username = username
    #     self.hashed_password = hashed_password
    #     self.role = role
    #     self.email = email
    #     self.status = status
    #     self.provider = provider
      

    @validator("status option")
    def validate_status(status, status_option):
        if status not in status_option:
            raise ValueError("Invalid status value")
