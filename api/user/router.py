from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from database import get_db
from api.auth import schema, crud, authutils, otp
from api.buyer.crud import NotFoundError
from typing import Optional, List
import uuid

router = APIRouter(
    prefix="/api/v1",
    tags=["Users"],
)



@router.get("/users", response_model=List[schema.UserReturn])
async def get_all_users(
    location_id: Optional[int] = Query(None, description="Filter users by location ID"),
    location_name: Optional[str] = Query(None, description="Filter users by location name"),
    db=Depends(get_db)
):
    """
    Get all users with optional location filtering.
    Users will include location_name information.
    """
    try:
        if location_id:
            users = crud.get_users_by_location(location_id, db)
        elif location_name:
            users = crud.get_users_by_location_name(location_name, db)
        else:
            users = crud.read_users(db)
        
        # Return empty list instead of raising 404 - this is more RESTful
        return users if users else []
        
    except NotFoundError:
        # This shouldn't happen with the current CRUD functions since they return []
        return []
    except Exception as e:
        print(f"Error in get_all_users: {str(e)}")  # Add logging
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving users: {str(e)}"
        )


@router.get("/admin", response_model=List[schema.UserReturn])
async def get_all_admin(db=Depends(get_db)):
    """Get all admin users with location information"""
    try:
        admins = crud.read_all_admin(db)
        if not admins:
            raise HTTPException(
                status_code=404,
                detail="There are no admins to display"
            )
        return admins
    except NotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"There are no admins to display: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving admins: {str(e)}"
        )


@router.get("/users/by-role/{role}")
async def get_users_by_role(
    role: str,
    location_id: Optional[int] = Query(None, description="Filter by location ID"),
    db=Depends(get_db)
):
    """Get users by role with optional location filtering"""
    try:
        if role not in ['admin', 'feeder', 'manager']:
            raise HTTPException(
                status_code=400,
                detail="Invalid role. Must be one of: admin, feeder, counter"
            )
        
        if location_id:
            users = crud.get_users_by_location(location_id, db)
            users = [user for user in users if user.role == role]
        else:
            users = crud.read_users(db)
            users = [user for user in users if user.role == role]
        
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving users by role: {str(e)}"
        )


@router.patch("/users/{user_id}", response_model=schema.UserReturn)
async def update_user_by_id(
    user_id: int, 
    user_info: schema.UserUpdate, 
    db=Depends(get_db)
):
    """Update user by ID and return updated user with location information"""
    try:
        # Check if user exists
        db_user = crud.find_user_by_id(user_id=user_id, db=db)
        if not db_user:
            raise HTTPException(
                status_code=404, 
                detail='User with this ID not found'
            )

        # Prepare update data
        update_data = user_info.model_dump(exclude_unset=True)
        print(f'New received data: {update_data}')

        # Update user
        updated_user = crud.update_user(user_id=user_id, updated_data=update_data, db=db)
        
        if not updated_user:
            raise HTTPException(
                status_code=404,
                detail="User not found during update"
            )
        
        return updated_user
        
    except crud.NotFoundError:
        raise HTTPException(
            status_code=404,
            detail="You are trying to update a user that does not exist."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating user: {str(e)}"
        )


@router.get("/users/{user_id}", response_model=schema.UserReturn)
async def read_user_by_id(user_id: int, db=Depends(get_db)):
    """Get user by ID with location information"""
    try:
        user = crud.find_user_by_id(user_id, db)
        if user is None:
            raise HTTPException(
                status_code=404, 
                detail="User does not exist"
            )
        return user
    except crud.NotFoundError:
        raise HTTPException(
            status_code=404, 
            detail="User does not exist"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving user: {str(e)}"
        )


@router.get("/users/me", response_model=schema.User)
async def read_current_user(current_user=Depends(authutils.get_current_user)):
    """Get current authenticated user"""
    print('Current user route accessed')
    return current_user


@router.get("/users/location/{location_id}", response_model=List[schema.UserReturn])
async def get_users_by_location_id(location_id: int, db=Depends(get_db)):
    """Get all users in a specific location by location ID"""
    try:
        users = crud.get_users_by_location(location_id, db)
        if not users:
            raise HTTPException(
                status_code=404,
                detail=f"No users found in location with ID {location_id}"
            )
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving users by location: {str(e)}"
        )


@router.get("/users/location/name/{location_name}", response_model=List[schema.UserReturn])
async def get_users_by_location_name(location_name: str, db=Depends(get_db)):
    """Get all users in a specific location by location name"""
    try:
        users = crud.get_users_by_location_name(location_name, db)
        # Return empty list instead of 404 - this is more RESTful
        return users if users else []
    except Exception as e:
        print(f"Error in get_users_by_location_name: {str(e)}")  # Add logging
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving users by location name: {str(e)}"
        )


@router.get("/test-auth")
async def test_auth(request: Request):
    """Test authentication header"""
    print("Headers:", request.headers)
    auth_header = request.headers.get("Authorization", "")
    return {"received_auth": auth_header}


@router.post("/forgot_password")
async def forgot_password(request: schema.ForgotPassword, db=Depends(get_db)):
    """Send password reset email"""
    try:
        user_reg = crud.find_user_by_email(request.email, db=db)
        if user_reg is None:
            raise HTTPException(
                status_code=404,
                detail="Email not registered"
            )
            
        # Create reset code and save in database
        reset_code = str(uuid.uuid4())
        crud.create_reset_code(email=request.email, reset_code=reset_code, db=db)

        print('Reset code generated:', reset_code)

        # Send email
        print(user_reg.username, 'requesting password reset')

        if user_reg.email:
            await otp.send_otp_to_user(
                subject=f"Password Reset - {user_reg.username}",
                body=f"Your password reset code is {reset_code}\nDo not share this code with anyone",
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
            detail="Email not registered",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except authutils.NoMatchError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication error",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except otp.EmailError:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while trying to send the email verification",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Something went wrong with the server: {str(e)}"
        )


@router.patch("/reset_password")
async def reset_password(request: schema.ResetPassword, db=Depends(get_db)):
    """Reset user password using reset token"""
    try:
        # Check valid reset password token
        reset_token = crud.check_reset_password_token(
            reset_password_token=request.reset_password_token, 
            db=db
        )
        print('Reset token found:', reset_token)

        # Check if new and confirm passwords match
        if request.new_password != request.confirm_password:
            raise HTTPException(
                status_code=400,
                detail="New password and confirm passwords do not match!"
            ) 
        
        # Reset new password
        forgot_password_object = schema.ForgotPassword(email=reset_token.email)
        new_hashed_password = authutils.get_password_hash(request.new_password)
        
        # Note: You'll need to implement these functions in crud
        await crud.reset_password(new_hashed_password, forgot_password_object.email, db)
        await crud.disable_reset_code(request.reset_password_token, forgot_password_object.email, db)

        return {
            "code": 200,
            "message": "Password has been reset successfully"
        }

    except crud.NotFoundError:
        raise HTTPException(
            status_code=404,
            detail="Reset password token has expired or is invalid"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Something went wrong: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user_by_id(user_id: int, db=Depends(get_db)):
    """Delete user by ID"""
    try:
        user = crud.find_user_by_id(user_id=user_id, db=db)
        if user is None:
            raise HTTPException(
                status_code=404,
                detail='User not found'
            )
        return crud.delete_user(user_id=user_id, db=db)
    except crud.NotFoundError:
        raise HTTPException(
            status_code=404,
            detail='User with this ID does not exist'
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting user: {str(e)}"
        )