from fastapi import APIRouter, Depends, HTTPException, status, Request
from database import get_db
from api.auth import schema, crud, authutils, otp
from api.buyer.crud import NotFoundError
import uuid

router = APIRouter(
    prefix="/api/v1",
    tags=["Users"],
)


@router.get("/users")
async def get_all_users(db=Depends(get_db)) -> list[schema.UserReturn]:
    try:
        # db_users = crud.read_users(db)
        # users = [schema.User(**db_user.__dict__) for db_user in db_users]
        # return users
        return crud.read_users(db)
    except NotFoundError as e:
        raise HTTPException(e, "there are no users to display")


@router.get("/admin")
async def get_all_admin(db=Depends(get_db)):
    try:
    # db_admin_list = crud.read_all_admin(db)
    # admin_list = [schema.User(**db_admin.__dict__) for db_admin in db_admin_list]
    # return admin_list
        return crud.read_all_admin(db)
    except NotFoundError as e:
        raise HTTPException(e, "there are no admins to display")



@router.patch("/users/{user_id: int}", response_model=schema.UserUpdate)
async def update_user_by_id(
    user_id: int, 
    user_info: schema.UserUpdate, 
    db=Depends(get_db)):
    try:
        db_user = crud.find_user_by_id(user_id=user_id, db=db)
        if not db_user:
            raise HTTPException(404, 'User with this ID not found')

        update_data = user_info.model_dump(exclude_unset=True)
        print(f'New received data: {update_data}')

        updated_user = crud.update_user(user_id=user_id, updated_data=update_data, db=db)
        return updated_user
        
    except crud.NotFoundError:
        raise HTTPException(
            status_code=404,
            detail="You are trying to update a user that does not exist."
        )

    return crud.update_user(user_id=user_id, updated_data=update_data.dict(exclude_unset=True), db=db)



@router.get("/users/me", response_model=schema.User)
async def read_current_user(current_user=Depends(authutils.get_current_user)):
    print('route accessed')
    return current_user


@router.get("/test-auth")
async def test_auth(request: Request):
    print("Headers:", request.headers)
    auth_header = request.headers.get("Authorization", "")
    return {"received_auth": auth_header}



@router.post("/forgot_password")
async def forgot_password(request: schema.ForgotPassword, db=Depends(get_db)):
    # check if user is registered
    try:
        user_reg = crud.find_user_by_email(request.email, db=db)
        if user_reg is None:
            raise HTTPException(
                    status_code=404,
                    detail="email not registered"
                )
            
            # create reset code and save in database
        reset_code = str(uuid.uuid4())
        crud.create_reset_code(email=request.email, reset_code=reset_code, db=db)

        print('this is reset code>>>>>>>', reset_code)

            # send email
        print(user_reg.username, '<<<<<<<<<')

        if user_reg.email:
            await otp.send_otp_to_user(
                subject=f"Hello {user_reg.email}",
                body=f"Your login OTP is {reset_code} \nDo not share this code with anyone",
                recipient_email=user_reg.email,
            )
        email = authutils.abfuscate_email(user_reg.email)
        return {
            "reset_code": reset_code,
            "code": 200,
            "message": f"We've sent an email with instructions to reset your password to {email}."
        }

    except crud.NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except authutils.NoMatchError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except otp.EmailError:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while trying to send the email verification",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"something went wrong with the server \n{e}"
        )


@router.patch("/reset_password")
async def reset_password(request: schema.ResetPassword, db=Depends(get_db)):
    try:
        # check valid reset password token
        reset_token = crud.check_reset_password_token(reset_password_token=request.reset_password_token, db=db)
        print(reset_token, '<<<<<<<<<<')
        # if reset_token is None:
        #     raise HTTPException(
        #         status_code=404,
        #         detail="Reset password token has expired, please request a new one"
        #     )

        # check both if new and confirm passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=404,
                detail="New password and confirm passwords do not match!"
            ) 
        
        # reset new password
        forgot_password_object = schema.ForgotPassword(**reset_token)
        new_hashed_password = authutils.get_password_hash(request.new_password)
        await crud.reset_password(new_hashed_password, forgot_password_object.email)

        # disable reset code when already used
        await crud.disable_reset_code(request.reset_password_token, forgot_password_object.email)

        return {
            "code": 200,
            "message": "Password has been reset successfully"
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"something went wrong with the server \n{e}"
        )


@router.delete("/{id: int}")
async def delete_user_by_id(id: int, db=Depends(get_db)):
    try:
        user = crud.find_user_by_id(user_id=id, db=db)
        if user is None:
            raise NotFoundError('user not found')
        return crud.delete_user(user_id=id, db=db)
    except NotFoundError:
        raise HTTPException(
            404,
            'user with this id does not exist'
        )