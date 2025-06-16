from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LocationBase(BaseModel):
    name: str
    address: Optional[str] = None
    region: Optional[str] = None
    status: str = 'active'

class LocationCreate(LocationBase):
    manager_id: Optional[int] = None

class LocationUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    manager_id: Optional[int] = None
    status: Optional[str] = None

class LocationList(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    region: Optional[str] = None
    status: str
    manager_id: Optional[int] = None

class LocationReturn(BaseModel):
    id: int
    name: str
    address: Optional[str] = None
    region: Optional[str] = None
    status: str
    manager_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True  # Updated from orm_mode for Pydantic V2

class LocationWithManager(LocationReturn):
    manager_name: Optional[str] = None  # Will be populated from the relationship

class LocationWithCoops(LocationReturn):
    total_coops: int = 0
    active_coops: int = 0

class UserInLocation(BaseModel):
    id: int
    username: str
    email: str
    role: str
    status: str
    
    class Config:
        from_attributes = True

class LocationWithUsers(LocationReturn):
    users: List[UserInLocation] = []

# NEW SCHEMAS FOR ASSIGNMENT FUNCTIONALITY
class CoopInLocation(BaseModel):
    id: int
    name: str
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class LocationWithCoopsDetailed(LocationReturn):
    coops: List[CoopInLocation] = []

class LocationFullDetails(LocationReturn):
    users: List[UserInLocation] = []
    coops: List[CoopInLocation] = []
    manager_name: Optional[str] = None

# Assignment request schemas
class AssignUserRequest(BaseModel):
    user_id: int

class AssignMultipleUsersRequest(BaseModel):
    user_ids: List[int]

class AssignCoopRequest(BaseModel):
    coop_id: int

class AssignMultipleCoopsRequest(BaseModel):
    coop_ids: List[int]

# Response schemas for assignments
class UserAssignmentResponse(BaseModel):
    user: UserInLocation
    message: str

class MultipleUsersAssignmentResponse(BaseModel):
    users: List[UserInLocation]
    message: str
    total_assigned: int

class CoopAssignmentResponse(BaseModel):
    coop: CoopInLocation
    message: str

class MultipleCoopsAssignmentResponse(BaseModel):
    coops: List[CoopInLocation]
    message: str
    total_assigned: int