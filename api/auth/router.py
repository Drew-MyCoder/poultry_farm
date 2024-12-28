from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from fastapi.responses import JSONResponse
from datetime import timedelta
from api.auth import authutils, schema, crud, otp, model
from database import get_db

router = APIRouter(
    prefix="/api/v1",
    tags=["Auth"]
)


@router.post("/auth/register")
def register(user: schema.UserList, db=Depends(get_db)
) -> schema.User:
    try:
        # db_user = model.DBUser(
        #     email=user.email,
        #     username=user.username,
        # )
        #  check if user exists
        result =  crud.get_user_by_email(email=user.email, db=db)
        if result:
            raise HTTPException(status_code=400, detail="Email already exists")

        # create new user
        print(user.password, " this is password<<<<<<<")
        hashed_password = authutils.get_password_hash(user.password)
        print(hashed_password, " this is hashed password<<<<<<<")

        # user.hashed_password = hashed_password
        # db_user = crud.create_user(db=db, db_user=user)
        db_user = model.DBUser(
            # id=user.id,
            username=user.username,
            password=hashed_password,
            status=user.status,
            email=user.email,
            role=user.role
        )

        added_user = crud.create_user(db=db, db_user=db_user)

        return added_user

    except authutils.CreationError as err:
        raise HTTPException(500, err)


@router.post("/login",)
async def login_for_otp(form_data: schema.UserLogin, db=Depends(get_db)):
    try:
        # user = authutils.authenticate_user(
        #     username=form_data.username, password=form_data.password, db=db
        # )
        # print(form_data.username, '>>>>>>>>>>>>>>>>>>>>')

        user = crud.find_by_username(username=form_data.username, db=db)

        print(form_data.username, '>>>>>>>>>>>>>>>>>>>>')

        one_time_pass = otp.generate_and_store_otp(user=user, db=db)
        if user.email:
            await otp.send_otp_to_user(
                subject="Poultry farm OTP",
                body=f"Your login OTP is {one_time_pass} \nDo not share this code with anyone",
                recipient_email=user.email,
            )
        email = authutils.abfuscate_email(user.email)
        return {
            "user": user.username,
            "message": f"Enter the 6-digit verification sent to {email}",
            "email": email,
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


@router.post("/verify")
async def verify_account_via_email(
    verification_details: schema.VerificationDetails, db=Depends(get_db)
):
    try:
        user = crud.find_by_username(username=verification_details.username, db=db)

        user_is_verified = otp.verify_otp(
            entered_otp=verification_details.otp, user=user, db=db
        )

        print(user.username, '<<<<<<<<<<<<<')

        if user_is_verified is False:
            raise HTTPException(400, "Invalid verification code")

        access_token_expires = timedelta(minutes=authutils.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = authutils.create_access_token(
            data={"sub": user.username, "roles": user.role},
            expires_delta=access_token_expires,
        )
        new_refresh_token = authutils.create_refresh_token(
            data={"sub": user.username}
        )

        response_data = {
            "token_type": "bearer",
            "user": user.username,
            "roles": user.role,
            "access_token": access_token,
        }

        response = JSONResponse(content=response_data)

        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="lax",
            # secure=True, # Only send over HTTPS
            # expires=timedelta(days=7), # Adjust expiration as needed    
        )

        return response
    except crud.NotFoundError as e:
        # raise HTTPException(
        #     status_code=404,
        #     detail="User verification failed",
        # ) from e
        print(e, ">>>>>>>>> here")
        


@router.get("/refresh")
async def refresh_access_token_endpoint(
    refresh_token=Cookie(..., httponly=True), db=Depends(get_db)
):
    try:
        username = await authutils.validate_refresh_token(
            db=db, refresh_token=refresh_token
        )

        user = crud.find_user_by_username(username=str(username), db=db)

        # if user.role is None:
        #     user.role = ["2001"] 
        role = user.role if user is not None else "feeder"
            # to change role key later

        access_token = authutils.create_access_token({"sub": username, "roles": role})
        print("this is the username >>>>>>>>>>", username)

        return {
            "access_token": access_token,
            "token)type": "bearer",
            "user": username,
            "roles": role
        }

    except crud.NotFoundError:
        raise HTTPException(401, {"Invalid user"})


@router.post("/logout")
async def log_user_out(refresh_token=Cookie(..., httponly=True), db=Depends(get_db)):
    authutils.blacklist_token(refresh_token, db=db)
    return {"message": "Successfully logged out"}