from fastapi import Depends
from database import get_db
from api.auth import model, schema
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timezone


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class NotFoundError(Exception):
    pass


def read_users(db):
    return db.query(model.DBUser).all()


def read_all_admin(db):
    return db.query(
        model.DBUser
    ).all()


def find_by_username(username: str, db):
    user = (
        db.query(model.DBUser)
        .filter(model.DBUser.username == username).first()
        )
    if user is None:
        raise NotFoundError(
            "user not found"
        )
    
    return (
        db.query(model.DBUser)
        .filter(model.DBUser.username == username)
        .first()
    )


def find_user_by_email(email: str, db):
    user = (db.query(model.DBUser).filter(model.DBUser.email == email).first())
    if user is None:
        raise NotFoundError(
            "email does not exist"
        )

    return (
        db.query(model.DBUser).filter(model.DBUser.email == email).first()
    )


def find_user_by_id(user_id: int, db) -> model.DBUser:
    if not db.query(model.DBUser).filter(model.DBUser.id == user_id).first():
        raise NotFoundError("User not found")

    return db.query(model.DBUser).filter(model.DBUser.id == user_id).first()


def find_user_by_username(username: str, db):
    user = (db.query(model.DBUser)
            .filter(model.DBUser.username == username)
            .first())
    if user is None:
        raise NotFoundError("{username.username} not found")


def get_user_by_email(email: str, db, provider: str = 'custom'):
    return (
        db.query(model.DBUser)
        .filter(
            model.DBUser.email == email, model.DBUser.provider == provider
        )
        .first()
    )


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
    return db_user


def create_user(db_user: model.DBUser, db: Session):
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return schema.User(**db_user.__dict__)


def update_user(db_user: model.DBUser, db):
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(user_id: int, db):
    user = db.query(model.DBUser).filter(model.DBUser.id == user_id).first()
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