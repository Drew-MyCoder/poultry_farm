from api.auth import model
from api.expenditure import schema, crud
from api.buyer.crud import NotFoundError, CreationError
from database import get_db
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(prefix="/expenditures", tags=["Expenditures"])


@router.post("expenditure")
async def create_new_expenditure(
    expenditure_detail: schema.ExpenditureCreate, db=Depends(get_db)
) -> schema.Expenditure:
    try:
        new_expenditure = model.DBExpenditure(
            id=expenditure_detail.id,
            amount=expenditure_detail.amount,
            reference=expenditure_detail.reference,
            user_id=expenditure_detail.user_id,
        )

        add_new_expenditure = crud.create_expenditure(new_expenditure, db)

        return{
            "id": add_new_expenditure.id,
            "amount": add_new_expenditure.amount,
            "reference": add_new_expenditure.reference,
            "user_id": add_new_expenditure.user_id,
        }

    except CreationError as err:
        raise HTTPException(500, err)


@router.get("/",)
async def get_all_expenditures(db=Depends(get_db)) -> list[schema.ExpenditureOutput]:
    try:
        return crud.read_expenditures(db)
    except NotFoundError as e:
        raise HTTPException(e, "there are no expenditures to display")


@router.get("/{id: int}")
async def get_expenditure_by_id(id: int, db=Depends(get_db)) -> schema.ExpenditureOutput:
    try:
        return crud.read_expenditure_by_id(id, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "expenditure does not exist")


@router.get("/{buyer_name: str}")
async def get_expenditure_by_name(expenditure_name: str, db=Depends(get_db)) -> schema.ExpenditureOutput:
    try:
        return crud.read_expenditure_by_name(expenditure_name, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "expenditure does not exist")


@router.delete("/{id: int}")
async def delete_expenditure_by_id(id: int, db=Depends(get_db)):
    try:
        expenditure = crud.find_expenditure_by_id(expenditure_id=id, db=db)
        if expenditure is None:
            raise NotFoundError('expenditure you are trying to delete does not exist')
        return crud.delete_expenditure(expenditure_id=id, db=db)
    except NotFoundError:
        raise HTTPException(
            404, "expenditure with this id does not exist")


@router.patch("/{id: int}", response_model=schema.ExpenditureUpdate)
async def update_buyer_by_id(
    id: int, update_expenditure: schema.ExpenditureUpdate, db=Depends(get_db)
):
    try:
        expenditure = crud.find_expenditure_by_id(id, db)
        if update_expenditure.amount:
            expenditure.amount = update_expenditure.amount
        if update_expenditure.reference:
            expenditure.reference = update_expenditure.reference
        
    except NotFoundError:
        raise HTTPException(
            404, "expenditure with this id cannot be updated"
        )

    return crud.update_expenditure(db_expenditure=expenditure, db=db)


