from fastapi import Depends
from database import get_db
from api.auth import model, schema
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import NotFoundError
from datetime import datetime, timezone


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def find_by_username(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)) -> model.DBUser:
    user = (
        db.query(model.DBUser)
        .filter(model.DBUser.username == form_data.username).first()
        )
    if user is None:
        raise NotFoundError(
            "{form_data.username} not found"
        )


def get_user_by_email(email: str, db, provider: str = 'customer'):
    return (
        db.query(model.DBUser)
        .filter(
            model.DBUser.email == email, model.DBUser.provider == provider
        )
        .first()
    )


def save_user(user: schema.UserCreate, db):
    new_user = model.DBUser(
        email=user.email,
        password=user.hashed_password,
        username=user.username,
        created_at=datetime.utcnow(),
        status='active'
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)  # Refresh to load the new data into the object.
    return new_user


def create_user(db_user: model.DBUser, db: Session):
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User {db_user} has been registered successfully"}


def update_user(db_user: model.DBUser, db):
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(user_id: int, db):
    user = db.query(model.DBUser).filter(model.DBUser.id == user_id).first()
    db.delete(user)
    db.commit()
    return {"message": f"user: {user_id} has been successfully deleted"}