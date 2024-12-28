from api.auth import model
from api.coop import schema, crud
from api.buyer.crud import NotFoundError, CreationError
from database import get_db
from fastapi import APIRouter, Depends, HTTPException


router = APIRouter(prefix="/coops", tags=["Coops"])


@router.post("coop", response_model=schema.Coop)
async def create_new_coop(
    coop_detail: schema.CoopCreate, db=Depends(get_db)
) -> schema.Coop:
    try:
        new_coop = model.DBCoops(
            # id=coop_detail.id,
            user_id=coop_detail.user_id,
            status='active',
            total_dead_fowls=coop_detail.total_dead_fowls,
            total_feed=coop_detail.total_feed,
            # total_old_fowls=coop_detail.total_old_fowls,
            total_fowls=coop_detail.total_fowls,
            coop_name=coop_detail.coop_name,
        )

        add_new_coop = crud.create_coop(db_coop=new_coop, db=db)
        return add_new_coop

        # return{
        #     "user_id": add_new_feed.user_id,
        #     "id": add_new_feed.id,
        #     "status": add_new_feed.status,
        #     "total_dead_fowls": add_new_feed.total_dead_fowls,
        #     "total_fowls": add_new_feed.total_fowls,
        #     "total_feed": add_new_feed.total_feed,
        #     "coop_name": add_new_feed.coop_name,
        #     # "total_young_fowls": add_new_feed.total_young_fowls
        # }

    except CreationError as err:
        raise HTTPException(500, err)


@router.get("/",)
async def get_all_coops(db=Depends(get_db)):
    try:
        db_coops = crud.read_coops(db)
        coops = [schema.Coop(**db_coop.__dict__) for db_coop in db_coops]
        return coops
    except NotFoundError as e:
        raise HTTPException(e, "there are no coops to display")


@router.get("/{id: int}")
async def get_coop_by_id(id: int, db=Depends(get_db)):
    try:
        return crud.read_coop_by_id(id, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "coop does not exist")


@router.get("/{coop_name: str}")
async def get_coop_by_coop_name(coop_name: str, db=Depends(get_db)):
    try:
        return crud.read_coop_by_coop_name(coop_name, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "coop does not exist")


@router.delete("/{id: int}")
async def delete_coop_by_id(id: int, db=Depends(get_db)):
    try:
        wallet = crud.find_coop_by_id(coop_id=id, db=db)
        if wallet is None:
            raise NotFoundError('coop you are trying to delete does not exist')
        return crud.delete_coop(coop_id=id, db=db)
    except NotFoundError:
        raise HTTPException(
            404, "coop with this id does not exist")


@router.patch("/{id: int}", response_model=schema.CoopUpdate)
async def daily_coop_update_by_id(
    id: int, update_coop: schema.CoopUpdate, db=Depends(get_db)
):
    try:
        coop = crud.find_coop_by_id(id, db)
        if update_coop.total_fowls:
            coop.total_fowls = update_coop.total_fowls
        if update_coop.total_dead_fowls:
            coop.total_dead_fowls = update_coop.total_dead_fowls
        if update_coop.total_feed:
            coop.total_feed = update_coop.total_feed
        if update_coop.coop_name:
            coop.coop_name = update_coop.coop_name

    except NotFoundError:
        raise HTTPException(
            404, "coop with this id cannot be updated"
        )

    return crud.update_coop(db_coop=coop, db=db)


@router.patch("/{id: int}", response_model=schema.CoopStatus)
async def update_coop_status_by_id(
    id: int, update_coop: schema.CoopStatus, db=Depends(get_db)
):
    try:
        coop = crud.find_coop_by_id(id, db)
        if update_coop.status:
            coop.status = update_coop.status
    
    except NotFoundError:
        raise HTTPException(
            404, "coop with this id cannot be updated"
        )

    return crud.update_coop(db_coop=coop, db=db)


@router.patch("/{id: int}", response_model=schema.CoopEgg)
async def update_coop_egg_by_id(
    id: int, update_coop: schema.CoopEgg, db=Depends(get_db)
):
    try:
        coop = crud.find_coop_by_id(id, db)
        if update_coop.egg_count:
            coop.egg_count = update_coop.egg_count
    
    except NotFoundError:
        raise HTTPException(
            404, "coop with this id cannot be updated"
        )

    return crud.update_coop(db_coop=coop, db=db)