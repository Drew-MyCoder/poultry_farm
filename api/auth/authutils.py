import os
import time
import uuid

from datetime import datetime, timedelta, UTC

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
from jwt import ExpiredSignatureError
from dotenv import load_dotenv
from . import crud, model
from database import get_db
from sqlalchemy.orm import Session
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
import logging

logger = logging.getLogger(__name__)


load_dotenv()

security = HTTPBearer()


# security settings
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRES_DAYS = 7

# security = HTTPBearer()

# Environment variable for production check
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


oauth2_scheme = OAuth2PasswordBearer("/token")

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


class NoMatchError(Exception):
    pass


class CreationError(Exception):
    pass

class InvalidTokenError(Exception):
    pass


# util functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict):
    to_encode = data.copy()
    
    # Ensure 'sub' is set to email
    if 'sub' not in to_encode:
        to_encode['sub'] = to_encode.get('email')  # Use email as subject
    
    # Add role if not present
    if 'role' not in to_encode:
        to_encode['role'] = 'feeder'  # Default role
    
    # Set expiration
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_token(token: str = Depends(oauth2_scheme)):
    return token

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db=Depends(get_db)
) -> model.DBUser:
    """
    Dependency to get current authenticated user from access token
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = crud.find_user_by_username(username=username, db=db)
    if user is None:
        raise credentials_exception
    
    return user

async def get_current_active_user(
    current_user: model.DBUser = Depends(get_current_user)
) -> model.DBUser:
    """
    Dependency to get current active user
    """
    if current_user.status != "active":
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def require_role(required_role: str):
    """
    Dependency factory to require specific user role
    """
    def role_checker(current_user: model.DBUser = Depends(get_current_active_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
        return current_user
    return role_checker


def login_for_access_token(user):
    if not crud.user or not verify_password(user.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(days=REFRESH_TOKEN_EXPIRES_DAYS)

    to_encode.update({"exp": expire})
    to_encode.update({"jti": str(uuid.uuid4())})

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def authenticate_user(username: str, password: str, db):
    user = crud.find_user_by_username(username=username, db=db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not exist"
        )

    if not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Password or email not found"
        )

    return user


def abfuscate_email(email, replacement_char="***"):
    parts = email.split("@")
    return f"{parts[0][:4]}{replacement_char}{parts[-1]}"


async def validate_refresh_token(db, refresh_token) -> str:
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=ALGORITHM)

        # validate expiry
        expire = payload.get("exp")
        if expire is None:
            raise JWTError()
        # convert current time to integer timestamp to enable comaprison
        now = int(time.mktime(datetime.now(UTC).utctimetuple()))

        if expire < now:
            raise ExpiredSignatureError()

        # validate jwt identifier
        jti = payload.get("jti")
        if jti is None:
            raise credentials_exception

        if crud.is_jti_blacklisted(jti, db):
            raise credentials_exception

        username = payload.get("sub")
        if username is None:
            raise credentials_exception

        return username
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=403,
            detail="Refresh token expired."
        )

    except JWTError:
        raise credentials_exception
    except crud.NotFoundError as err:
        raise HTTPException(401, err)


def blacklist_token(token: str, db=Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        jti = payload.get("jti", "")
        db_jti = model.DBBlacklistedToken(jti)
        crud.revoke_jti(db_jti=db_jti, db=db)
    except JWTError:
        raise credentials_exception


class LoginSecurityManager:
    def __init__(
        self,
        max_attempts: int = 5,
        lockout_duration_minutes: int = 15,
        attempt_window_minutes: int = 60
    ):
        self.max_attempts = max_attempts
        self.lockout_duration_minutes = lockout_duration_minutes
        self.attempt_window_minutes = attempt_window_minutes
    
    def check_account_status(self, db: Session, username: str) -> dict:
        """
        Check if account can attempt login
        Returns dict with status info
        """
        # Clean up expired lockouts first
        crud.LoginAttemptsCRUD.cleanup_expired_lockouts(db)
        
        # Check if account is currently locked
        is_locked, lockout = crud.LoginAttemptsCRUD.is_account_locked(db, username)
        
        if is_locked and lockout:
            remaining_time = lockout.unlock_at - datetime.utcnow()
            remaining_minutes = int(remaining_time.total_seconds() / 60)
            
            return {
                "can_attempt": False,
                "is_locked": True,
                "unlock_at": lockout.unlock_at,
                "remaining_minutes": max(0, remaining_minutes),
                "failed_attempts": lockout.failed_attempts
            }
        
        # Check recent failed attempts
        since = datetime.utcnow() - timedelta(minutes=self.attempt_window_minutes)
        failed_count = crud.LoginAttemptsCRUD.get_failed_attempts_count(db, username, since)
        
        return {
            "can_attempt": failed_count < self.max_attempts,
            "is_locked": False,
            "failed_attempts": failed_count,
            "attempts_remaining": max(0, self.max_attempts - failed_count)
        }
    
    def record_failed_attempt(
        self,
        db: Session,
        username: str,
        request: Optional[Request] = None,
        failure_reason: str = "Invalid credentials"
    ):
        """Record a failed login attempt and lock account if necessary"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Record the attempt
        crud.LoginAttemptsCRUD.record_login_attempt(
            db=db,
            username=username,
            success=False,
            ip_address=ip_address,
            user_agent=user_agent,
            failure_reason=failure_reason
        )
        
        # Check if we need to lock the account
        since = datetime.utcnow() - timedelta(minutes=self.attempt_window_minutes)
        failed_count = crud.LoginAttemptsCRUD.get_failed_attempts_count(db, username, since)
        
        if failed_count >= self.max_attempts:
            crud.LoginAttemptsCRUD.lock_account(
                db=db,
                username=username,
                lockout_duration_minutes=self.lockout_duration_minutes,
                failed_attempts=failed_count
            )
            
            logger.warning(
                f"Account locked due to {failed_count} failed attempts: {username}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Account locked due to too many failed attempts. "
                       f"Try again in {self.lockout_duration_minutes} minutes."
            )
        
        return {
            "failed_attempts": failed_count,
            "attempts_remaining": self.max_attempts - failed_count
        }
    
    def record_successful_attempt(
        self,
        db: Session,
        username: str,
        request: Optional[Request] = None
    ):
        """Record a successful login attempt and reset failed attempts"""
        ip_address = None
        user_agent = None
        
        if request:
            ip_address = request.client.host if request.client else None
            user_agent = request.headers.get("user-agent")
        
        # Record successful attempt
        crud.LoginAttemptsCRUD.record_login_attempt(
            db=db,
            username=username,
            success=True,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Reset failed attempts
        crud.LoginAttemptsCRUD.reset_failed_attempts(db, username)
    
    def validate_can_attempt_login(self, db: Session, username: str):
        """Validate if user can attempt login, raise exception if not"""
        status = self.check_account_status(db, username)
        
        if not status["can_attempt"]:
            if status["is_locked"]:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Account is locked. Try again in {status['remaining_minutes']} minutes."
                )
            else:
                remaining = status.get("attempts_remaining", 0)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed attempts. {remaining} attempts remaining."
                )
