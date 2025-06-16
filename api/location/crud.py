from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from api.auth.model import DBLocation, DBUser, DBCoops  # Import your models
from api.location.schema import LocationCreate, LocationUpdate


class LocationCRUD:
    
    @staticmethod
    def create_location(db: Session, location: LocationCreate) -> DBLocation:
        """Create a new location"""
        db_location = DBLocation(
            name=location.name,
            address=location.address,
            region=location.region,
            manager_id=location.manager_id,
            status=location.status
        )
        db.add(db_location)
        db.commit()
        db.refresh(db_location)
        return db_location
    
    @staticmethod
    def get_location(db: Session, location_id: int) -> Optional[DBLocation]:
        """Get a location by ID"""
        return db.query(DBLocation).filter(DBLocation.id == location_id).first()
    
    @staticmethod
    def get_location_by_name(db: Session, name: str) -> Optional[DBLocation]:
        """Get a location by name"""
        return db.query(DBLocation).filter(DBLocation.name == name).first()
    
    @staticmethod
    def get_locations(db: Session, skip: int = 0, limit: int = 100) -> List[DBLocation]:
        """Get all locations with pagination"""
        return db.query(DBLocation).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_locations_by_status(db: Session, status: str, skip: int = 0, limit: int = 100) -> List[DBLocation]:
        """Get locations by status"""
        return db.query(DBLocation).filter(DBLocation.status == status).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_locations_by_region(db: Session, region: str, skip: int = 0, limit: int = 100) -> List[DBLocation]:
        """Get locations by region"""
        return db.query(DBLocation).filter(DBLocation.region == region).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_location(db: Session, location_id: int, location_update: LocationUpdate) -> Optional[DBLocation]:
        """Update a location"""
        db_location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not db_location:
            return None
        
        update_data = location_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_location, field, value)
        
        db.commit()
        db.refresh(db_location)
        return db_location
    
    @staticmethod
    def delete_location(db: Session, location_id: int) -> bool:
        """Delete a location"""
        db_location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not db_location:
            return False
        
        db.delete(db_location)
        db.commit()
        return True
    
    @staticmethod
    def get_location_with_manager(db: Session, location_id: int) -> Optional[dict]:
        """Get location with manager details"""
        result = db.query(
            DBLocation,
            DBUser.username
        ).outerjoin(
            DBUser, DBLocation.manager_id == DBUser.id
        ).filter(DBLocation.id == location_id).first()
        
        if not result:
            return None
        
        location, manager_name = result
        return {
            "location": location,
            "manager_name": manager_name
        }
    
    @staticmethod
    def get_location_with_coops_count(db: Session, location_id: int) -> Optional[dict]:
        """Get location with coop statistics"""
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return None
        
        total_coops = db.query(func.count(DBCoops.id)).filter(DBCoops.location_id == location_id).scalar()
        active_coops = db.query(func.count(DBCoops.id)).filter(
            DBCoops.location_id == location_id,
            DBCoops.status == 'active'
        ).scalar()
        
        return {
            "location": location,
            "total_coops": total_coops or 0,
            "active_coops": active_coops or 0
        }
    
    @staticmethod
    def assign_manager(db: Session, location_id: int, manager_id: int) -> Optional[DBLocation]:
        """Assign a manager to a location"""
        # Check if manager exists
        manager = db.query(DBUser).filter(DBUser.id == manager_id).first()
        if not manager:
            return None
        
        # Update location
        db_location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not db_location:
            return None
        
        db_location.manager_id = manager_id
        db.commit()
        db.refresh(db_location)
        return db_location
    
    @staticmethod
    def get_locations_managed_by_user(db: Session, manager_id: int) -> List[DBLocation]:
        """Get all locations managed by a specific user"""
        return db.query(DBLocation).filter(DBLocation.manager_id == manager_id).all()
    
    @staticmethod
    def search_locations(db: Session, search_term: str, skip: int = 0, limit: int = 100) -> List[DBLocation]:
        """Search locations by name, address, or region"""
        search_pattern = f"%{search_term}%"
        return db.query(DBLocation).filter(
            (DBLocation.name.ilike(search_pattern)) |
            (DBLocation.address.ilike(search_pattern)) |
            (DBLocation.region.ilike(search_pattern))
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_location_with_users(db: Session, location_id: int) -> Optional[dict]:
        """Get location with all associated users"""
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return None
        
        # Get all users associated with this location
        users = db.query(DBUser).filter(DBUser.location_id == location_id).all()
        
        return {
            "location": location,
            "users": users
        }

    @staticmethod
    def get_users_by_location(db: Session, location_id: int) -> List[DBUser]:
        """Get all users in a specific location"""
        return db.query(DBUser).filter(DBUser.location_id == location_id).all()

    @staticmethod
    def get_users_by_location_and_role(db: Session, location_id: int, role: str) -> List[DBUser]:
        """Get users in a location filtered by role"""
        return db.query(DBUser).filter(
            DBUser.location_id == location_id,
            DBUser.role == role
        ).all()

    # NEW METHODS FOR USER ASSIGNMENT
    @staticmethod
    def assign_user_to_location(db: Session, location_id: int, user_id: int) -> Optional[DBUser]:
        """Assign a user to a location"""
        # Check if location exists
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return None
        
        # Check if user exists
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not user:
            return None
        
        # Update user's location
        user.location_id = location_id
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def assign_multiple_users_to_location(db: Session, location_id: int, user_ids: List[int]) -> List[DBUser]:
        """Assign multiple users to a location"""
        # Check if location exists
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return []
        
        # Get all valid users
        users = db.query(DBUser).filter(DBUser.id.in_(user_ids)).all()
        if not users:
            return []
        
        # Update all users' location
        updated_users = []
        for user in users:
            user.location_id = location_id
            updated_users.append(user)
        
        db.commit()
        for user in updated_users:
            db.refresh(user)
        
        return updated_users

    @staticmethod
    def remove_user_from_location(db: Session, user_id: int) -> Optional[DBUser]:
        """Remove a user from their current location"""
        user = db.query(DBUser).filter(DBUser.id == user_id).first()
        if not user:
            return None
        
        user.location_id = None
        db.commit()
        db.refresh(user)
        return user

    # NEW METHODS FOR COOP ASSIGNMENT
    @staticmethod
    def assign_coop_to_location(db: Session, location_id: int, coop_id: int) -> Optional[DBCoops]:
        """Assign a coop to a location"""
        # Check if location exists
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return None
        
        # Check if coop exists
        coop = db.query(DBCoops).filter(DBCoops.id == coop_id).first()
        if not coop:
            return None
        
        # Update coop's location
        coop.location_id = location_id
        db.commit()
        db.refresh(coop)
        return coop

    @staticmethod
    def assign_multiple_coops_to_location(db: Session, location_id: int, coop_ids: List[int]) -> List[DBCoops]:
        """Assign multiple coops to a location"""
        # Check if location exists
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return []
        
        # Get all valid coops
        coops = db.query(DBCoops).filter(DBCoops.id.in_(coop_ids)).all()
        if not coops:
            return []
        
        # Update all coops' location
        updated_coops = []
        for coop in coops:
            coop.location_id = location_id
            updated_coops.append(coop)
        
        db.commit()
        for coop in updated_coops:
            db.refresh(coop)
        
        return updated_coops

    @staticmethod
    def remove_coop_from_location(db: Session, coop_id: int) -> Optional[DBCoops]:
        """Remove a coop from its current location"""
        coop = db.query(DBCoops).filter(DBCoops.id == coop_id).first()
        if not coop:
            return None
        
        coop.location_id = None
        db.commit()
        db.refresh(coop)
        return coop

    @staticmethod
    def get_coops_by_location(db: Session, location_id: int, skip: int = 0, limit: int = 100) -> List[DBCoops]:
        """Get all coops in a specific location"""
        return db.query(DBCoops).filter(DBCoops.location_id == location_id).offset(skip).limit(limit).all()

    @staticmethod
    def get_coops_by_location_and_status(db: Session, location_id: int, status: str, skip: int = 0, limit: int = 100) -> List[DBCoops]:
        """Get coops in a location filtered by status"""
        return db.query(DBCoops).filter(
            DBCoops.location_id == location_id,
            DBCoops.status == status
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_location_with_full_details(db: Session, location_id: int) -> Optional[dict]:
        """Get location with all associated users and coops"""
        location = db.query(DBLocation).filter(DBLocation.id == location_id).first()
        if not location:
            return None
        
        # Get all users and coops for this location
        users = db.query(DBUser).filter(DBUser.location_id == location_id).all()
        coops = db.query(DBCoops).filter(DBCoops.location_id == location_id).all()
        
        # Get manager details
        manager = db.query(DBUser).filter(DBUser.id == location.manager_id).first() if location.manager_id else None
        
        return {
            "location": location,
            "users": users,
            "coops": coops,
            "manager": manager
        }