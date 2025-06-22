from api.auth import model
from api.expenditure import schema, crud
from api.expenditure.crud import NotFoundError, CreationError
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from typing import List

router = APIRouter(prefix="/expenditures", tags=["Expenditures"])


@router.post("/", response_model=schema.Expenditure)
async def create_new_expenditure(
    expenditure_detail: schema.ExpenditureCreate, db=Depends(get_db)
) -> schema.Expenditure:
    try:
        new_expenditure = model.DBExpenditure(
            amount=expenditure_detail.amount,
            reference=expenditure_detail.reference,
            category=expenditure_detail.category,
            payment_method=expenditure_detail.payment_method,
            status=expenditure_detail.status,
            approved_by=expenditure_detail.approved_by,
            user_id=expenditure_detail.user_id,
            location_id=expenditure_detail.location_id,
        )

        add_new_expenditure = crud.create_expenditure(new_expenditure, db)

        return {
            "id": add_new_expenditure.id,
            "amount": add_new_expenditure.amount,
            "reference": add_new_expenditure.reference,
            "category": add_new_expenditure.category,
            "payment_method": add_new_expenditure.payment_method,
            "status": add_new_expenditure.status,
            "approved_by": add_new_expenditure.approved_by,
            "user_id": add_new_expenditure.user_id,
        }

    except CreationError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/", response_model=List[schema.ExpenditureOutput])
async def get_all_expenditures(db=Depends(get_db)):
    try:
        expenditures = crud.read_expenditures(db)
        if not expenditures:
            return []
        return expenditures
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditures: {str(e)}")


@router.get("/user/{user_id}", response_model=List[schema.ExpenditureOutput])
async def get_expenditures_by_user(user_id: int, db=Depends(get_db)):
    try:
        expenditures = crud.read_expenditures_by_user(user_id, db)
        if not expenditures:
            raise HTTPException(status_code=404, detail="No expenditures found for this user")
        return expenditures
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditures: {str(e)}")


@router.get("/location/{location_id}", response_model=List[schema.ExpenditureOutput])
async def get_expenditures_by_location(location_id: int, db=Depends(get_db)):
    try:
        expenditures = crud.read_expenditures_by_location(location_id, db)
        if not expenditures:
            raise HTTPException(status_code=404, detail="No expenditures found for this location")
        return expenditures
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Expenditure with this location does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditures: {str(e)}")


@router.get("/category/{category}", response_model=List[schema.ExpenditureOutput])
async def get_expenditures_by_category(category: str, db=Depends(get_db)):
    try:
        expenditures = crud.read_expenditures_by_category(category, db)
        if not expenditures:
            raise HTTPException(status_code=404, detail="No expenditures found for this category")
        return expenditures
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Expenditure with this category does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditures: {str(e)}")


@router.get("/status/{status}", response_model=List[schema.ExpenditureOutput])
async def get_expenditures_by_status(status: str, db=Depends(get_db)):
    try:
        expenditures = crud.read_expenditures_by_status(status, db)
        if not expenditures:
            raise HTTPException(status_code=404, detail="No expenditures found with this status")
        return expenditures
    except NotFoundError as e:
        raise HTTPException(e, "expenditure with this staus does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditures: {str(e)}")


@router.get("/{expenditure_id}", response_model=schema.ExpenditureOutput)
async def get_expenditure_by_id(expenditure_id: int, db=Depends(get_db)):
    try:
        expenditure = crud.read_expenditure_by_id(expenditure_id, db)
        if expenditure is None:
            raise HTTPException(status_code=404, detail="Expenditure not found")
        return expenditure
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Expenditure with this id does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditure: {str(e)}")


@router.get("/reference/{reference}", response_model=schema.ExpenditureOutput)
async def get_expenditure_by_reference(reference: str, db=Depends(get_db)):
    try:
        return crud.read_expenditure_by_reference(reference, db)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail="Expenditure not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditure: {str(e)}")


@router.delete("/{expenditure_id}")
async def delete_expenditure_by_id(expenditure_id: int, db=Depends(get_db)):
    try:
        expenditure = crud.find_expenditure_by_id(expenditure_id, db)
        if expenditure:
            return crud.delete_expenditure(expenditure_id, db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Expenditure with this id does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting expenditure: {str(e)}")


@router.patch("/{expenditure_id}", response_model=schema.ExpenditureOutput)
async def update_expenditure_by_id(
    expenditure_id: int, update_expenditure: schema.ExpenditureUpdate, db=Depends(get_db)
):
    try:
        expenditure = crud.find_expenditure_by_id(expenditure_id, db)
        
        # Update fields only if they are provided in the request
        if update_expenditure.reference:
            expenditure.reference = update_expenditure.reference
        if update_expenditure.category:
            expenditure.category = update_expenditure.category
        if update_expenditure.payment_method:
            expenditure.payment_method = update_expenditure.payment_method
        if update_expenditure.status:
            expenditure.status = update_expenditure.status
        if update_expenditure.approved_by:
            expenditure.approved_by = update_expenditure.approved_by

        return crud.update_expenditure(db_expenditure=expenditure, db=db)

    except NotFoundError:
        raise HTTPException(
            status_code=404, detail="Expenditure with this id cannot be updated"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating expenditure: {str(e)}")