import os
import time
import uuid

from datetime import datetime, timedelta, UTC

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status, Request
from jwt import PyJWTError, ExpiredSignatureError
from pydantic import ValidationError
from dotenv import load_dotenv
from . import crud, model
from api.auth import schema
from database import get_db
from sqlalchemy.orm import Session


load_dotenv()


# security settings
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "")
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRES_DAYS = 7


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


# util functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()
#     if not expires_delta:
#         expires_delta = timedelta(minutes=15)

#     expire: datetime = datetime.now(UTC) + expires_delta

#     to_encode.update({"exp": expire})
#     to_encode.update({"jti": str(uuid.uuid4())})

#     encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

#     return encode_jwt

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

# In login route
# access_token = create_access_token({
#     "email": user.email,
#     "sub": user.email,  # Explicitly set sub to email
#     "role": user.role
# })


def get_user_token(token: str = Depends(oauth2_scheme)):
    return token


async def get_current_user( 
    request: Request, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db) ):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    print("Request Header:", request.headers)
    print(f"Received token: {token}")  # Debugging step
    
    if not token:
        print('No token received')
        raise credentials_exception
    print(f'received token: {token}')

    try:
        print(f'Received token: {token}')
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print('Decoded payload: ', payload)
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        user = crud.find_user_by_email(db=db, email=username)
        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        return user  # ✅ Return the user object
        # return {"username": username, "role": role}
    except JWTError as e:
        print('jwt decoding failed: ', str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )

        # # check blacklist token
        # blacklist_token = await crud.find_blaclist_token(token)
        # if blacklist_token:
        #     raise credentials_exception

        # # check if user exist
        # result = await crud.find_exist_user(username)
        # if not result:
        #     raise HTTPException(
        #         status_code=status.HTTP_404_NOT_FOUND,
        #         detail="User not registered."
        #     )
        # return schema.UserList(**result)
    

    except (PyJWTError, ValidationError):
        raise credentials_exception


def login_for_access_token(user):
    if not crud.user or not verify_password(user.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username, "role": user.role.value})
    return {"access_token": access_token, "token_type": "bearer"}


def role_required(required_role: model.DBUser.role):
    def role_dependency(current_user: dict = Depends(get_current_user)):
        if current_user["role"] != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
            )
        return current_user
    return role_dependency


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