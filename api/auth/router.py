from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
import NotFoundError
from api.auth import authutils, schema, model, crud
from database import get_db

router = APIRouter(
    prefix="/api/v1",
    tags=["Auth"]
)


@router.post("/auth/register", response_model=schema.UserList)
def register(user: schema.UserCreate, db=Depends(get_db)
):
    # db_user = model.DBUser(
    #     email=user.email,
    #     username=user.username,
    # )
    #  check if user exists
    result =  crud.get_user_by_email(email=user.email, db=db)
    if result:
        raise NotFoundError(status_code=409, detail="User already exist")

    # create new user
    user.hashed_password = authutils.get_password_hash(user.hashed_password)
    crud.save_user(user, db=db)

    return {**user.dict()}