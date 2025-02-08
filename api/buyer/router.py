from api.auth import model
from api.buyer import schema, crud
from api.buyer.crud import NotFoundError, CreationError
from database import get_db
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(prefix="/buyers", tags=["Buyers"])


@router.post("/buyer")
async def create_new_buyer(
    buyer_detail: schema.BuyerCreate, db=Depends(get_db)
) -> schema.Buyer:
    try:
        new_buyer = model.DBBuyer(
            # id=buyer_detail.id,
            name=buyer_detail.name,
            crates_desired=buyer_detail.crates_desired,
            date_of_delivery=buyer_detail.date_of_delivery,
            amount=buyer_detail.amount,
            status_of_delivery=buyer_detail.status_of_delivery,
        )

        add_new_feed = crud.create_buyer(new_buyer, db)

        return{
            "id": add_new_feed.id,
            "name": add_new_feed.name,
            "crates_desired": add_new_feed.crates_desired,
            "date_of_delivery": add_new_feed.date_of_delivery,
            "amount": add_new_feed.amount,
            "status_of_delivery": add_new_feed.status_of_delivery,
        }

    except CreationError as err:
        raise HTTPException(500, err)


@router.get("/",)
async def get_all_buyers(db=Depends(get_db)) -> list[schema.BuyerOutput]:
    try:
        return crud.read_buyers(db)
    except NotFoundError as e:
        raise HTTPException(e, "there are no buyers to display")


@router.get("/{id: int}")
async def get_buyer_by_id(id: int, db=Depends(get_db)) -> schema.BuyerOutput:
    try:
        return crud.read_buyer_by_id(id, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "buyer does not exist")


@router.get("/{buyer_name: str}")
async def get_buyer_by_name(buyer_name: str, db=Depends(get_db)) -> schema.BuyerOutput:
    try:
        return crud.read_buyer_by_name(buyer_name, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "buyer does not exist")


@router.delete("/{id: int}")
async def delete_buyer_by_id(id: int, db=Depends(get_db)):
    try:
        buyer = crud.find_buyer_by_id(coop_id=id, db=db)
        if buyer is None:
            raise NotFoundError('buyer you are trying to delete does not exist')
        return crud.delete_buyer(buyer_id=id, db=db)
    except NotFoundError:
        raise HTTPException(
            404, "buyer with this id does not exist")


@router.patch("/{id: int}", response_model=schema.BuyerUpdate)
async def update_buyer_by_id(
    id: int, update_buyer: schema.BuyerUpdate, db=Depends(get_db)
):
    try:
        buyer = crud.find_buyer_by_id(id, db)
        if update_buyer.amount:
            buyer.amount = update_buyer.amount
        if update_buyer.crates_desired:
            buyer.crates_desired = update_buyer.crates_desired
        if update_buyer.date_of_delivery:
            buyer.date_of_delivery = update_buyer.date_of_delivery
        if update_buyer.status_of_delivery:
            buyer.status_of_delivery = update_buyer.status_of_delivery

    except NotFoundError:
        raise HTTPException(
            404, "coop with this id cannot be updated"
        )

    return crud.update_buyer(db_buyer=buyer, db=db)


