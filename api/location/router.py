from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from database import get_db  # Your database dependency
from api.location.schema import (
    LocationCreate, LocationUpdate, LocationReturn, LocationWithUsers,
    LocationList, LocationWithManager, LocationWithCoops, UserInLocation,
    LocationWithCoopsDetailed, LocationFullDetails, CoopInLocation,
    AssignUserRequest, AssignMultipleUsersRequest, AssignCoopRequest, AssignMultipleCoopsRequest,
    UserAssignmentResponse, MultipleUsersAssignmentResponse, CoopAssignmentResponse, MultipleCoopsAssignmentResponse
)
from api.location.crud import LocationCRUD

router = APIRouter(prefix="/locations", tags=["locations"])


@router.post("/", response_model=LocationReturn, status_code=status.HTTP_201_CREATED)
def create_location(
    location: LocationCreate,
    db: Session = Depends(get_db)
):
    """Create a new location"""
    # Check if location name already exists
    existing_location = LocationCRUD.get_location_by_name(db, location.name)
    if existing_location:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Location with this name already exists"
        )
    
    return LocationCRUD.create_location(db, location)


@router.get("/", response_model=List[LocationList])
def get_locations(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str = Query(None, description="Filter by status"),
    region_filter: str = Query(None, description="Filter by region"),
    search: str = Query(None, description="Search by name, address, or region"),
    db: Session = Depends(get_db)
):
    """Get all locations with optional filters"""
    if search:
        return LocationCRUD.search_locations(db, search, skip, limit)
    elif status_filter:
        return LocationCRUD.get_locations_by_status(db, status_filter, skip, limit)
    elif region_filter:
        return LocationCRUD.get_locations_by_region(db, region_filter, skip, limit)
    else:
        return LocationCRUD.get_locations(db, skip, limit)


@router.get("/{location_id}", response_model=LocationReturn)
def get_location(location_id: int, db: Session = Depends(get_db)):
    """Get a specific location by ID"""
    location = LocationCRUD.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    return location


@router.get("/{location_id}/with-manager", response_model=LocationWithManager)
def get_location_with_manager(location_id: int, db: Session = Depends(get_db)):
    """Get location with manager details"""
    result = LocationCRUD.get_location_with_manager(db, location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    location_data = LocationWithManager.model_validate(result["location"])
    location_data.manager_name = result["manager_name"]
    return location_data


@router.get("/{location_id}/with-coops", response_model=LocationWithCoops)
def get_location_with_coops(location_id: int, db: Session = Depends(get_db)):
    """Get location with coop statistics"""
    result = LocationCRUD.get_location_with_coops_count(db, location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    location_data = LocationWithCoops.model_validate(result["location"])
    location_data.total_coops = result["total_coops"]
    location_data.active_coops = result["active_coops"]
    return location_data


@router.put("/{location_id}", response_model=LocationReturn)
def update_location(
    location_id: int,
    location_update: LocationUpdate,
    db: Session = Depends(get_db)
):
    """Update a location"""
    updated_location = LocationCRUD.update_location(db, location_id, location_update)
    if not updated_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    return updated_location


@router.delete("/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(location_id: int, db: Session = Depends(get_db)):
    """Delete a location"""
    success = LocationCRUD.delete_location(db, location_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )


@router.post("/{location_id}/assign-manager/{manager_id}", response_model=LocationReturn)
def assign_manager_to_location(
    location_id: int,
    manager_id: int,
    db: Session = Depends(get_db)
):
    """Assign a manager to a location"""
    updated_location = LocationCRUD.assign_manager(db, location_id, manager_id)
    if not updated_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location or manager not found"
        )
    return updated_location


@router.get("/manager/{manager_id}", response_model=List[LocationList])
def get_locations_by_manager(manager_id: int, db: Session = Depends(get_db)):
    """Get all locations managed by a specific user"""
    return LocationCRUD.get_locations_managed_by_user(db, manager_id)


@router.get("/{location_id}/with-users", response_model=LocationWithUsers)
def get_location_with_users(location_id: int, db: Session = Depends(get_db)):
    """Get location with all associated users"""
    result = LocationCRUD.get_location_with_users(db, location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    location_data = LocationWithUsers.model_validate(result["location"])
    location_data.users = [UserInLocation.model_validate(user) for user in result["users"]]
    return location_data


@router.get("/{location_id}/users", response_model=List[UserInLocation])
def get_users_in_location(
    location_id: int, 
    role: str = Query(None, description="Filter by user role"),
    db: Session = Depends(get_db)
):
    """Get all users in a specific location, optionally filtered by role"""
    if role:
        users = LocationCRUD.get_users_by_location_and_role(db, location_id, role)
    else:
        users = LocationCRUD.get_users_by_location(db, location_id)
    
    return [UserInLocation.model_validate(user) for user in users]


# NEW ROUTES FOR USER ASSIGNMENT
@router.post("/{location_id}/assign-user", response_model=UserAssignmentResponse)
def assign_user_to_location(
    location_id: int,
    request: AssignUserRequest,
    db: Session = Depends(get_db)
):
    """Assign a single user to a location"""
    user = LocationCRUD.assign_user_to_location(db, location_id, request.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location or user not found"
        )
    
    return UserAssignmentResponse(
        user=UserInLocation.model_validate(user),
        message=f"User successfully assigned to location"
    )


@router.post("/{location_id}/assign-users", response_model=MultipleUsersAssignmentResponse)
def assign_multiple_users_to_location(
    location_id: int,
    request: AssignMultipleUsersRequest,
    db: Session = Depends(get_db)
):
    """Assign multiple users to a location"""
    users = LocationCRUD.assign_multiple_users_to_location(db, location_id, request.user_ids)
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or no valid users provided"
        )
    
    return MultipleUsersAssignmentResponse(
        users=[UserInLocation.model_validate(user) for user in users],
        message=f"{len(users)} users successfully assigned to location",
        total_assigned=len(users)
    )


@router.delete("/users/{user_id}/remove-from-location", response_model=UserAssignmentResponse)
def remove_user_from_location(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Remove a user from their current location"""
    user = LocationCRUD.remove_user_from_location(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserAssignmentResponse(
        user=UserInLocation.model_validate(user),
        message="User successfully removed from location"
    )


# NEW ROUTES FOR COOP ASSIGNMENT
@router.get("/{location_id}/coops", response_model=List[CoopInLocation])
def get_coops_in_location(
    location_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status_filter: str = Query(None, description="Filter by coop status"),
    db: Session = Depends(get_db)
):
    """Get all coops in a specific location, optionally filtered by status"""
    if status_filter:
        coops = LocationCRUD.get_coops_by_location_and_status(db, location_id, status_filter, skip, limit)
    else:
        coops = LocationCRUD.get_coops_by_location(db, location_id, skip, limit)
    
    return [CoopInLocation.model_validate(coop) for coop in coops]


@router.get("/{location_id}/with-coops-detailed", response_model=LocationWithCoopsDetailed)
def get_location_with_coops_detailed(location_id: int, db: Session = Depends(get_db)):
    """Get location with detailed coop information"""
    location = LocationCRUD.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    coops = LocationCRUD.get_coops_by_location(db, location_id)
    
    location_data = LocationWithCoopsDetailed.model_validate(location)
    location_data.coops = [CoopInLocation.model_validate(coop) for coop in coops]
    return location_data


@router.post("/{location_id}/assign-coop", response_model=CoopAssignmentResponse)
def assign_coop_to_location(
    location_id: int,
    request: AssignCoopRequest,
    db: Session = Depends(get_db)
):
    """Assign a single coop to a location"""
    coop = LocationCRUD.assign_coop_to_location(db, location_id, request.coop_id)
    if not coop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location or coop not found"
        )
    
    return CoopAssignmentResponse(
        coop=CoopInLocation.model_validate(coop),
        message="Coop successfully assigned to location"
    )


@router.post("/{location_id}/assign-coops", response_model=MultipleCoopsAssignmentResponse)
def assign_multiple_coops_to_location(
    location_id: int,
    request: AssignMultipleCoopsRequest,
    db: Session = Depends(get_db)
):
    """Assign multiple coops to a location"""
    coops = LocationCRUD.assign_multiple_coops_to_location(db, location_id, request.coop_ids)
    if not coops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found or no valid coops provided"
        )
    
    return MultipleCoopsAssignmentResponse(
        coops=[CoopInLocation.model_validate(coop) for coop in coops],
        message=f"{len(coops)} coops successfully assigned to location",
        total_assigned=len(coops)
    )


@router.delete("/coops/{coop_id}/remove-from-location", response_model=CoopAssignmentResponse)
def remove_coop_from_location(
    coop_id: int,
    db: Session = Depends(get_db)
):
    """Remove a coop from its current location"""
    coop = LocationCRUD.remove_coop_from_location(db, coop_id)
    if not coop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Coop not found"
        )
    
    return CoopAssignmentResponse(
        coop=CoopInLocation.model_validate(coop),
        message="Coop successfully removed from location"
    )


@router.get("/{location_id}/full-details", response_model=LocationFullDetails)
def get_location_full_details(location_id: int, db: Session = Depends(get_db)):
    """Get location with complete details including users, coops, and manager"""
    result = LocationCRUD.get_location_with_full_details(db, location_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    location_data = LocationFullDetails.model_validate(result["location"])
    location_data.users = [UserInLocation.model_validate(user) for user in result["users"]]
    location_data.coops = [CoopInLocation.model_validate(coop) for coop in result["coops"]]
    location_data.manager_name = result["manager"].username if result["manager"] else None
    
    return location_data


# BULK OPERATIONS
@router.post("/{location_id}/bulk-assign", status_code=status.HTTP_200_OK)
def bulk_assign_to_location(
    location_id: int,
    user_ids: List[int] = Query(None, description="List of user IDs to assign"),
    coop_ids: List[int] = Query(None, description="List of coop IDs to assign"),
    db: Session = Depends(get_db)
):
    """Bulk assign users and coops to a location"""
    # Check if location exists
    location = LocationCRUD.get_location(db, location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )
    
    results = {}
    
    # Assign users if provided
    if user_ids:
        assigned_users = LocationCRUD.assign_multiple_users_to_location(db, location_id, user_ids)
        results["users"] = {
            "assigned": [UserInLocation.model_validate(user) for user in assigned_users],
            "count": len(assigned_users)
        }
    
    # Assign coops if provided
    if coop_ids:
        assigned_coops = LocationCRUD.assign_multiple_coops_to_location(db, location_id, coop_ids)
        results["coops"] = {
            "assigned": [CoopInLocation.model_validate(coop) for coop in assigned_coops],
            "count": len(assigned_coops)
        }
    
    if not user_ids and not coop_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one of user_ids or coop_ids must be provided"
        )
    
    return {
        "message": "Bulk assignment completed successfully",
        "location_id": location_id,
        "results": results
    }