from fastapi import APIRouter, Depends, HTTPException, status, Cookie, Request
from fastapi.responses import JSONResponse
from api.auth import authutils, schema, crud, otp, model
from database import get_db
import logging

logger = logging.getLogger(__name__)

login_security = authutils.LoginSecurityManager(
    max_attempts=5,
    lockout_duration_minutes=15,
    attempt_window_minutes=60
)

router = APIRouter(
    prefix="/api/v1",
    tags=["Auth"]
)


@router.get("/me")
async def get_current_user(current_user: model.DBUser = Depends(authutils.get_current_user)):
    """Get current authenticated user information"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "status": current_user.status
    }


@router.post("/auth/register")
def register(user: schema.UserList, db=Depends(get_db)
) -> schema.User:
    try:
        #  check if user exists
        result =  crud.get_user_by_email(email=user.email, db=db)
        if result:
            raise HTTPException(status_code=400, detail="Email already exists")

        # create new user
        # print(user.password, " this is password<<<<<<<")
        hashed_password = authutils.get_password_hash(user.password)
        # print(hashed_password, " this is hashed password<<<<<<<")

        # user.hashed_password = hashed_password
        # db_user = crud.create_user(db=db, db_user=user)
        db_user = model.DBUser(
            # id=user.id,
            username=user.username,
            password=hashed_password,
            status='active',
            email=user.email,
            role='feeder'
        )

        added_user = crud.create_user(db=db, db_user=db_user)

        return added_user

    except authutils.CreationError as err:
        raise HTTPException(500, err)


@router.post("/login")
async def login_for_otp(
    form_data: schema.UserLogin, 
    request: Request,
    db=Depends(get_db)
):
    """Initiate login process with OTP verification and attempt tracking"""
    try:
        # Input validation
        if not form_data.username:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username is required"
            )
        
        # Check if account can attempt login
        login_security.validate_can_attempt_login(db, form_data.username)
        
        try:
            user = crud.find_by_username(username=form_data.username, db=db)
        except crud.NotFoundError:
            # Record failed attempt for non-existent user
            login_security.record_failed_attempt(
                db=db,
                username=form_data.username,
                request=request,
                failure_reason="User not found"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if account is active
        if user.status != 'active':
            login_security.record_failed_attempt(
                db=db,
                username=form_data.username,
                request=request,
                failure_reason="Account inactive"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )
        
        # Generate and send OTP
        one_time_pass = otp.generate_and_store_otp(user=user, db=db)

        print(one_time_pass, 'otp herre')
        
        if not user.email:
            login_security.record_failed_attempt(
                db=db,
                username=form_data.username,
                request=request,
                failure_reason="No email address"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email address associated with this account"
            )
        
        try:
            await otp.send_otp_to_user(
                subject="Poultry Farm - Login Verification",
                body=f"Your login verification code is: {one_time_pass}\n\n"
                     f"This code will expire in 10 minutes.\n"
                     f"Do not share this code with anyone.\n\n"
                     f"If you didn't request this code, please ignore this email.",
                recipient_email=user.email,
            )
            logger.info(f"OTP sent successfully to user: {form_data.username}")
        except otp.EmailError as email_err:
            logger.error(f"Email sending failed for user {form_data.username}: {email_err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to send verification email. Please try again or contact support."
            )
        
        email = authutils.abfuscate_email(user.email)
        return {
            "user": user.username,
            "message": f"Enter the 6-digit verification code sent to {email}",
            "email": email,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected server error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An unexpected error occurred. Please try again."
        )



@router.post("/verify")
async def verify_account_via_email(
    verification_details: schema.VerificationDetails,
    request: Request,
    db=Depends(get_db)
):
    """Verify OTP and complete login process with attempt tracking"""
    try:
        # Input validation
        if not verification_details.username or not verification_details.otp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username and OTP are required"
            )
        
        # Check if account can attempt verification
        login_security.validate_can_attempt_login(db, verification_details.username)
        
        try:
            user = crud.find_by_username(username=verification_details.username, db=db)
        except crud.NotFoundError:
            login_security.record_failed_attempt(
                db=db,
                username=verification_details.username,
                request=request,
                failure_reason="User not found during verification"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Check if account is still active
        if user.status != 'active':
            login_security.record_failed_attempt(
                db=db,
                username=verification_details.username,
                request=request,
                failure_reason="Account inactive during verification"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active"
            )
        
        # Verify OTP
        user_is_verified = otp.verify_otp(
            entered_otp=verification_details.otp, user=user, db=db
        )
        
        if not user_is_verified:
            login_security.record_failed_attempt(
                db=db,
                username=verification_details.username,
                request=request,
                failure_reason="Invalid OTP"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification code"
            )
        
        # Record successful login
        login_security.record_successful_attempt(
            db=db,
            username=verification_details.username,
            request=request
        )
        
        # Create tokens
        access_token = authutils.create_access_token(
            data={"sub": user.username, "roles": user.role}
        )
        new_refresh_token = authutils.create_refresh_token(
            data={"sub": user.username}
        )
        
        response_data = {
            "token_type": "bearer",
            "user": user.username,
            "roles": user.role,
            "access_token": access_token,
            "user_id": user.id,
        }
        
        response = JSONResponse(content=response_data)
        
        # Set secure cookie
        response.set_cookie(
            key="refresh_token",
            value=new_refresh_token,
            httponly=True,
            samesite="lax",
            secure=True if authutils.ENVIRONMENT == "production" else False,
            max_age=7 * 24 * 60 * 60,  # 7 days
        )
        
        logger.info(f"User successfully logged in: {user.username}")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
@router.post("/refresh")
async def refresh_access_token_endpoint(
    refresh_token: str = Cookie(None, alias="refresh_token"), db=Depends(get_db)
):

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found"
        )

    try:
        username = await authutils.validate_refresh_token(
            db=db, refresh_token=refresh_token
        )

        user = crud.find_user_by_username(username=str(username), db=db)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        role = user.role if user is not None else "feeder"

        access_token = authutils.create_access_token({"sub": username, "roles": role})
        # print("this is the username >>>>>>>>>>", username)
        # print("this is the refresh token >>>>>>>>>>", access_token)

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": username,
            "roles": role
        }

    except (crud.NotFoundError, authutils.InvalidTokenError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )


@router.post("/logout")
async def log_user_out(
    refresh_token: str = Cookie(None, alias="refresh_token"), 
    db=Depends(get_db)
):
    if refresh_token:
        authutils.blacklist_token(refresh_token, db=db)
    
    response = JSONResponse(content={"message": "Successfully logged out"})
    
    # Clear the refresh token cookie
    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        samesite="lax"
    )
    
    return response


# Admin endpoint to check account status
@router.get("/admin/account-status/{username}")
async def get_account_status(
    username: str,
    current_user: model.DBUser = Depends(authutils.get_current_user),
    db=Depends(get_db)
):
    """Get account lockout status (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    status = login_security.check_account_status(db, username)
    recent_attempts = authutils.LoginAttemptsCRUD.get_recent_attempts(db, username, hours=24)
    
    return {
        "username": username,
        "status": status,
        "recent_attempts": len(recent_attempts),
        "last_attempt": recent_attempts[0].attempt_time if recent_attempts else None
    }

# Admin endpoint to unlock account
@router.post("/admin/unlock-account/{username}")
async def unlock_account(
    username: str,
    current_user: model.DBUser = Depends(authutils.get_current_user),
    db=Depends(get_db)
):
    """Manually unlock an account (admin only)"""
    if current_user.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    unlocked = authutils.LoginAttemptsCRUD.unlock_account(db, username)
    
    if unlocked:
        logger.info(f"Account manually unlocked by admin {current_user.username}: {username}")
        return {"message": f"Account {username} has been unlocked"}
    else:
        return {"message": f"Account {username} was not locked"}