from api.auth import model
from database import get_db
from api.buyer.crud import NotFoundError
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException


def read_role(user_id: int, db):
    admin_role = (db.query(
        model.DBUser
        ).filter(model.DBUser.id == user_id)
        .first()
    )
    if admin_role is None:
        raise NotFoundError(
            404,
            'no admin found'
        )
    else:
        return admin_role
        