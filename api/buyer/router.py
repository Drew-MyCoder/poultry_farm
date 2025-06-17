from api.auth import model
from api.buyer import schema, crud
from api.buyer.crud import NotFoundError, CreationError
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from typing import List



router = APIRouter(prefix="/buyers", tags=["Buyers"])


@router.post("/", response_model=schema.Buyer)
async def create_new_buyer(
    buyer_detail: schema.BuyerCreate, 
    db=Depends(get_db),
) -> schema.Buyer:
    try:
         # CHECK TO SEE IF ROLE IS ROLE
        # if role != "feeder":
        #     raise HTTPException(status_code=404,
        #     detail='you are not authorized to create a buyer')
            
        new_buyer = model.DBBuyer(
            # id=buyer_detail.id,
            name=buyer_detail.name,
            crates_desired=buyer_detail.crates_desired,
            date_of_delivery=buyer_detail.date_of_delivery,
            amount=buyer_detail.amount,
            status_of_delivery=buyer_detail.status_of_delivery,
            by=buyer_detail.by,
            location_id=buyer_detail.location_id
        )

        add_new_feed = crud.create_buyer(new_buyer, db)

        return{
            "id": add_new_feed.id,
            "name": add_new_feed.name,
            "crates_desired": add_new_feed.crates_desired,
            "date_of_delivery": add_new_feed.date_of_delivery,
            "amount": add_new_feed.amount,
            "status_of_delivery": add_new_feed.status_of_delivery,
            "by": add_new_feed.by,
        }

    except CreationError as err:
        raise HTTPException(500, detail=f"Unexpected error: {str(err)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/", response_model=List[schema.BuyerOutput])
async def get_all_buyers(db=Depends(get_db)):
    # try:
    #     return crud.read_buyers(db)
    # except NotFoundError as e:
    #     raise HTTPException(e, "there are no buyers to display")
    try:
        buyer = crud.read_buyers(db)
        if not buyer:
            raise HTTPException(status_code=404, detail="No buyer found")
        return buyer
    except NotFoundError as e:
        raise HTTPException(500, detail=f"Unexpected error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving buyer: {str(e)}")


@router.get("/{id: int}", response_model=schema.BuyerOutput)
async def get_buyer_by_id(id: int, db=Depends(get_db)):
    # try:
    #     return crud.read_buyer_by_id(id, db=db)
    # except NotFoundError as e:
    #     raise HTTPException(e, "buyer does not exist")
    try:
        buyer = crud.read_buyer_by_id(id, db)
        if buyer is None:
            raise HTTPException(status_code=404, detail="Buyer not found")
        return buyer
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Buyer with this id does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving buyer: {str(e)}")


@router.get("/{buyer_name: str}", response_model=List[schema.BuyerOutput])
async def get_buyer_by_name(buyer_name: str, db=Depends(get_db)):
    # try:
    #     return crud.read_buyer_by_name(buyer_name, db=db)
    # except NotFoundError as e:
    #     raise HTTPException(e, "buyer does not exist")
    try:
        buyers = crud.read_buyer_by_name(buyer_name, db)
        if not buyers:
            raise HTTPException(status_code=404, detail="No buyers found with this status")
        return buyers
    except NotFoundError as e:
        raise HTTPException(e, "buyer with this staus does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving expenditures: {str(e)}")



@router.delete("/{id: int}")
async def delete_buyer_by_id(buyer_id: int, db=Depends(get_db)):
    # try:
    #     buyer = crud.find_buyer_by_id(buyer_id=id, db=db)
    #     if buyer is None:
    #         raise NotFoundError('buyer you are trying to delete does not exist')
    #     return crud.delete_buyer(buyer_id=id, db=db)
    # except NotFoundError:
    #     raise HTTPException(
    #         404, "buyer with this id does not exist")
    try:
        buyer = crud.find_buyer_by_id(buyer_id, db)
        if buyer:
            return crud.delete_buyer(buyer_id, db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Buyer with this id does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting buyer: {str(e)}")


@router.patch("/{buyer_id: int}", response_model=schema.BuyerOutput)
async def update_buyer_by_id(
    buyer_id: int, update_buyer: schema.BuyerUpdate, db=Depends(get_db)
):
    # try:
    #     buyer = crud.find_buyer_by_id(id, db=db)

    #     if not buyer:
    #         raise HTTPException(404, "Buyer with this ID not found")

    #     update_data = update_buyer.dict(exclude_unset=True)  # Exclude fields not provided
    #     updated_buyer = crud.update_buyer(buyer_id=id, updated_data=update_data, db=db)
    #     return updated_buyer

    # except NotFoundError:
    #     raise HTTPException(
    #         404, "buyer with this id cannot be updated"
    #     )

    # return crud.update_buyer(buyer_id=id, updated_data=update_buyer.dict(exclude_unset=True), db=db)
    try:
        buyer = crud.find_buyer_by_id(buyer_id, db)
        
        # Update fields only if they are provided in the request
        if update_buyer.crates_desired:
            buyer.crates_desired = update_buyer.crates_desired
        if update_buyer.date_of_delivery:
            buyer.date_of_delivery = update_buyer.date_of_delivery
        if update_buyer.status_of_delivery:
            buyer.status_of_delivery = update_buyer.status_of_delivery

        return crud.update_buyer(db_buyer=buyer, db=db)

    except NotFoundError:
        raise HTTPException(
            status_code=404, detail="Expenditure with this id cannot be updated"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating buyer: {str(e)}")


@router.get("/location/{location_id}", response_model=List[schema.BuyerOutput])
async def get_buyer_by_location(location_id: int, db=Depends(get_db)):
    try:
        buyer = crud.read_buyer_by_location(location_id, db)
        if not buyer:
            raise HTTPException(status_code=404, detail="No buyer found for this location")
        return buyer
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Buyer with this location does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving buyer: {str(e)}")




