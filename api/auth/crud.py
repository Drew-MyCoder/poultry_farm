from sqlalchemy.orm import joinedload
from api.auth import model, schema
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
import logging
from typing import Optional, List


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class NotFoundError(Exception):
    pass


def read_users(db):
    """Get all users with their location information"""
    return db.query(model.DBUser).options(joinedload(model.DBUser.location)).all()


def read_all_admin(db):
    """Get all admin users with their location information"""
    return (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(model.DBUser.role == 'admin')
            .all())


def read_feeder_role(db):
    """Get first feeder user with location information"""
    feeder = (db.query(model.DBUser)
              .options(joinedload(model.DBUser.location))
              .filter(model.DBUser.role == 'feeder')
              .first())
    print(f'feeder found: {feeder}')
    if feeder is None:
        return None
    return feeder


def find_by_username(username: str, db):
    """Find user by username with location information"""
    user = (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(model.DBUser.username == username)
            .first())
    if user is None:
        raise NotFoundError("user not found")
    
    return user


def find_user_by_email(email: str, db):
    """Find user by email with location information"""
    user = (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(model.DBUser.email == email)
            .first())
    if user is None:
        raise NotFoundError("email does not exist")

    return user


def find_user_by_id(user_id: int, db) -> model.DBUser:
    """Find user by ID with location information"""
    user = (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(model.DBUser.id == user_id)
            .first())
    if not user:
        raise NotFoundError("User not found")

    return user


def find_user_by_username(username: str, db):
    """Find user by username (alternative method)"""
    user = (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(model.DBUser.username == username)
            .first())
    if user is None:
        raise NotFoundError(f"{username} not found")
    return user


def get_user_by_email(email: str, db, provider: str = 'custom'):
    """Get user by email and provider with location information"""
    return (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(
                model.DBUser.email == email, 
                model.DBUser.provider == provider
            )
            .first())


def get_users_by_location(location_id: int, db):
    try:
        # First check if location exists
        location = db.query(model.DBLocation).filter(model.DBLocation.id == location_id).first()
        print(f"Location {location_id} exists: {location is not None}")
        
        users = (db.query(model.DBUser)
                .options(joinedload(model.DBUser.location))
                .filter(model.DBUser.location_id == location_id)
                .all())
        
        print(f"Found {len(users)} users for location_id {location_id}")
        return users
        
    except Exception as e:
        print(f"Error in get_users_by_location: {str(e)}")
        import traceback
        traceback.print_exc()  # This will show the full stack trace
        raise


def get_users_by_location_name(location_name: str, db):
    """Get all users for a specific location by location name"""
    try:
        # Method 1: Using explicit join condition
        users = (db.query(model.DBUser)
                .join(model.DBLocation, model.DBUser.location_id == model.DBLocation.id)
                .options(joinedload(model.DBUser.location))
                .filter(model.DBLocation.name == location_name)
                .all())
        
        print(f"Found {len(users)} users for location '{location_name}'")
        return users
        
    except Exception as e:
        print(f"Error in get_users_by_location_name: {str(e)}")
        # Fallback method using subquery
        try:
            location = db.query(model.DBLocation).filter(model.DBLocation.name == location_name).first()
            if not location:
                print(f"No location found with name: {location_name}")
                return []
            
            users = (db.query(model.DBUser)
                    .options(joinedload(model.DBUser.location))
                    .filter(model.DBUser.location_id == location.id)
                    .all())
            
            print(f"Fallback method found {len(users)} users for location '{location_name}'")
            return users
            
        except Exception as fallback_error:
            print(f"Fallback method also failed: {str(fallback_error)}")
            raise e


def create_reset_code(email: str, reset_code: str, db: Session):
    new_code = model.DBReset(email=email, reset_code=reset_code)
    db.add(new_code)
    db.commit()
    db.refresh(new_code)
    return new_code


def save_user(db: Session, db_user: schema.UserCreate):  
    user_data = db_user.dict() if hasattr(db_user, "dict") else db_user
    db_user = model.DBUser(**user_data)  # Map Pydantic model to SQLAlchemy model
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Load the location relationship after creation
    db.refresh(db_user)
    user_with_location = (db.query(model.DBUser)
                         .options(joinedload(model.DBUser.location))
                         .filter(model.DBUser.id == db_user.id)
                         .first())
    return user_with_location


def create_user(db_user: model.DBUser, db: Session):
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    # Load the location relationship after creation
    user_with_location = (db.query(model.DBUser)
                         .options(joinedload(model.DBUser.location))
                         .filter(model.DBUser.id == db_user.id)
                         .first())
    return schema.User(**user_with_location.__dict__)


def update_user(user_id: int, updated_data: dict, db: Session):
    """Update user with location information included in response"""
    user = (db.query(model.DBUser)
            .options(joinedload(model.DBUser.location))
            .filter(model.DBUser.id == user_id)
            .first())

    if not user:
        return None
    
    print('received updated data', updated_data)
    for key, value in updated_data.items():
        if value is not None and value != 'string':
            print(f'updating {key} to {value}')
            setattr(user, key, value)

    db.commit()
    db.refresh(user)
    # Reload with location information after update
    updated_user = (db.query(model.DBUser)
                   .options(joinedload(model.DBUser.location))
                   .filter(model.DBUser.id == user_id)
                   .first())
    return updated_user

def delete_user(user_id: int, db):
    user = db.query(model.DBUser).filter(model.DBUser.id == user_id).first()
    if not user:
        raise NotFoundError("User not found")
    
    db.delete(user)
    db.commit()
    return {"message": f"user: {user_id} has been successfully deleted"}


def revoke_jti(db_jti: model.DBBlacklistedToken, db: Session):
    db.add(db_jti)
    db.commit()
    db.refresh(db_jti)


def is_jti_blacklisted(jti: str, db: Session) -> bool:
    blacklisted_token = (
        db.query(model.DBBlacklistedToken)
        .filter(model.DBBlacklistedToken.jti == jti)  # type: ignore
        .first()
    )

    return str(blacklisted_token) == jti


def check_reset_password_token(reset_password_token: str, db: Session):
    # ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)

    token = db.query(model.DBReset).filter(
        # model.DBReset.status == '',
        model.DBReset.reset_code == reset_password_token,
        # model.DBReset.expired >= ten_minutes_ago
    ).first()
    
    if token is None:
        raise NotFoundError('no token was found')

    print(token, 'this is token <<<<<<<<')
    print(token.reset_code, 'this is reset code <<<<<<<')
    return token


logger = logging.getLogger(__name__)

class LoginAttemptsCRUD:
    
    @staticmethod
    def record_login_attempt(
        db: Session,
        username: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        failure_reason: Optional[str] = None
    ) -> model.LoginAttempt:
        """Record a login attempt"""
        attempt = model.LoginAttempt(
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            failure_reason=failure_reason
        )
        db.add(attempt)
        db.commit()
        db.refresh(attempt)
        return attempt
    
    @staticmethod
    def get_failed_attempts_count(
        db: Session,
        username: str,
        since: datetime
    ) -> int:
        """Get count of failed login attempts since a specific time"""
        return db.query(model.LoginAttempt).filter(
            model.LoginAttempt.username == username,
            not model.LoginAttempt.success,
            model.LoginAttempt.attempt_time >= since
        ).count()
    
    @staticmethod
    def get_recent_attempts(
        db: Session,
        username: str,
        hours: int = 1
    ) -> List[model.LoginAttempt]:
        """Get recent login attempts for a user"""
        since = datetime.utcnow() - timedelta(hours=hours)
        return db.query(model.LoginAttempt).filter(
            model.LoginAttempt.username == username,
            model.LoginAttempt.attempt_time >= since
        ).order_by(model.LoginAttempt.attempt_time.desc()).all()
    
    @staticmethod
    def lock_account(
        db: Session,
        username: str,
        lockout_duration_minutes: int = 15,
        failed_attempts: int = 0
    ) -> model.AccountLockout:
        """Lock an account for a specified duration"""
        unlock_at = datetime.utcnow() + timedelta(minutes=lockout_duration_minutes)
        
        # Check if lockout already exists
        existing_lockout = db.query(model.AccountLockout).filter(
            model.AccountLockout.username == username,
            model.AccountLockout.is_active
        ).first()
        
        if existing_lockout:
            # Update existing lockout
            existing_lockout.locked_at = datetime.utcnow()
            existing_lockout.unlock_at = unlock_at
            existing_lockout.failed_attempts = failed_attempts
            lockout = existing_lockout
        else:
            # Create new lockout
            lockout = model.AccountLockout(
                username=username,
                unlock_at=unlock_at,
                failed_attempts=failed_attempts
            )
            db.add(lockout)
        
        db.commit()
        db.refresh(lockout)
        logger.warning(f"Account locked: {username} until {unlock_at}")
        return lockout
    
    @staticmethod
    def is_account_locked(db: Session, username: str) -> tuple[bool, Optional[model.AccountLockout]]:
        """Check if an account is currently locked"""
        lockout = db.query(model.AccountLockout).filter(
            model.AccountLockout.username == username,
            model.AccountLockout.is_active,
            model.AccountLockout.unlock_at > datetime.utcnow()
        ).first()
        
        return (lockout is not None, lockout)
    
    @staticmethod
    def unlock_account(db: Session, username: str) -> bool:
        """Manually unlock an account or clean up expired lockouts"""
        lockouts = db.query(model.AccountLockout).filter(
            model.AccountLockout.username == username,
            model.AccountLockout.is_active
        ).all()
        
        unlocked = False
        for lockout in lockouts:
            lockout.is_active = False
            unlocked = True
        
        if unlocked:
            db.commit()
            logger.info(f"Account unlocked: {username}")
        
        return unlocked
    
    @staticmethod
    def cleanup_expired_lockouts(db: Session) -> int:
        """Clean up expired lockouts"""
        expired_lockouts = db.query(model.AccountLockout).filter(
            model.AccountLockout.is_active,
            model.AccountLockout.unlock_at <= datetime.utcnow()
        ).all()
        
        count = len(expired_lockouts)
        for lockout in expired_lockouts:
            lockout.is_active = False
        
        if count > 0:
            db.commit()
            logger.info(f"Cleaned up {count} expired lockouts")
        
        return count
    
    @staticmethod
    def reset_failed_attempts(db: Session, username: str):
        """Reset failed attempts counter after successful login"""
        LoginAttemptsCRUD.unlock_account(db, username)