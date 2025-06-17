from api.auth import model
from api.coop import schema, crud
from api.buyer.crud import NotFoundError, CreationError
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List



router = APIRouter(prefix="/coops", tags=["Coops"])


@router.post("/", response_model=schema.Coop)
async def create_new_coop(
    coop_detail: schema.CoopCreate, db=Depends(get_db)
) -> schema.CoopCreate:
    try:
        # check if user is admin
        # is_admin = utils.admin_status(user_id=coop_detail.user_id, db=db)
        
        new_coop = model.DBCoops(
            # id=coop_detail.id,
            user_id=coop_detail.user_id,
            status='active',
            total_dead_fowls=coop_detail.total_dead_fowls,
            total_feed=coop_detail.total_feed,
            # total_old_fowls=coop_detail.total_old_fowls,
            total_fowls=coop_detail.total_fowls,
            coop_name=coop_detail.coop_name,
            collection_date=coop_detail.collection_date,
            remainder_eggs=coop_detail.remainder_eggs,
            notes=coop_detail.notes,
            efficiency=coop_detail.efficiency,
            egg_count=coop_detail.egg_count,
            location_id=coop_detail.location_id,
        )
        
        add_new_coop = crud.create_coop(db_coop=new_coop, db=db)
        # return add_new_coop
        # print(add_new_coop.user_id, '<<<this is the user id')
        # print(add_new_coop.id, '<<<this is the id')

        return{
            "user_id": add_new_coop.user_id,
            "id": add_new_coop.id,
            "parent_id": add_new_coop.parent_id,
            "status": 'active',
            "total_dead_fowls": add_new_coop.total_dead_fowls,
            "total_fowls": add_new_coop.total_fowls,
            "total_feed": add_new_coop.total_feed,
            "coop_name": add_new_coop.coop_name,
            "collection_date": add_new_coop.collection_date,
            "remainder_eggs": add_new_coop.remainder_eggs,
            "notes": add_new_coop.notes,
            "efficiency": add_new_coop.efficiency,
            "egg_count": add_new_coop.egg_count,
            # "total_young_fowls": add_new_feed.total_young_fowls
        }

    except CreationError as err:
        raise HTTPException(status_code=500, detail=str(err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.get("/",)
async def get_all_coops(db=Depends(get_db)) -> list[schema.CoopOutput]:
    try:
        return crud.read_coops(db)
    except NotFoundError as e:
        raise HTTPException(e, "there are no coops to display")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")



@router.get("/{coop_id: int}", response_model=schema.CoopOutput)
async def get_coop_by_id(coop_id: int, db=Depends(get_db)):
    # try:
    #     return crud.read_coop_by_id(id, db=db)
    # except NotFoundError as e:
    #     raise HTTPException(e, "coop does not exist")
    try:
        coop = crud.read_coop_by_id(coop_id, db)
        if coop is None:
            raise HTTPException(status_code=404, detail="coop not found")
        return coop
    except NotFoundError:
        raise HTTPException(status_code=404, detail="coop with this id does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving coop: {str(e)}")


@router.get("/{coop_name: str}/history", response_model=list[schema.CoopUpdate])
async def get_coop_by_coop_name(coop_name: str, db=Depends(get_db)):
    try:
        return crud.read_coop_by_coop_name(coop_name, db=db)
    except NotFoundError as e:
        raise HTTPException(e, "coop does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving coop: {str(e)}")



@router.delete("/{coop_id: int}")
async def delete_coop_by_id(coop_id: int, db=Depends(get_db)):
    try:
        coop = crud.find_coop_by_id(coop_id, db=db)
    #     if coop is None:
    #         raise NotFoundError('coop you are trying to delete does not exist')
    #     return crud.delete_coop(coop_id=id, db=db)
    # except NotFoundError:
    #     raise HTTPException(
    #         404, "coop with this id does not exist"
        if coop:
            return crud.delete_coop(coop_id, db)
    except NotFoundError:
        raise HTTPException(status_code=404, detail="coop with this id does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting coop: {str(e)}")



@router.patch("/{coop_id: int}", response_model=schema.CoopUpdate)
async def daily_coop_update_by_id(
    coop_id: int, update_coop: schema.CoopUpdate, db=Depends(get_db)
):
    try:
        coop = crud.find_coop_by_id(coop_id, db=db)
        print(coop, '<<<<this is the coop')
        if update_coop.total_fowls:
            coop.total_fowls = update_coop.total_fowls
        if update_coop.total_dead_fowls:
            coop.total_dead_fowls = update_coop.total_dead_fowls
        if update_coop.total_feed:
            coop.total_feed = update_coop.total_feed
        if update_coop.coop_name:
            coop.coop_name = update_coop.coop_name
        if update_coop.egg_count:
            coop.egg_count = update_coop.egg_count
        if update_coop.crates_collected:
            coop.crates_collected = update_coop.crates_collected
        if update_coop.remainder_eggs:
            coop.remainder_eggs = update_coop.remainder_eggs
        if update_coop.broken_eggs:
            coop.broken_eggs = update_coop.broken_eggs
        if update_coop.notes:
            coop.notes = update_coop.notes
        if update_coop.efficiency:
            coop.efficiency = update_coop.efficiency

        return crud.update_coop(db_coop=coop, db=db)

    except NotFoundError:
        raise HTTPException(
            404, "coop with this id cannot be updated"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating coop: {str(e)}")


@router.patch("/{coop_id}", response_model=schema.CoopUpdate)
async def update_coop(coop_id: int, coop_update: schema.DailyCoopUpdate, db: Session = Depends(get_db)):
    try:
        # fetch existing record
        existing_coop = crud.read_coop_by_id(coop_id, db=db)

        if not existing_coop:
            raise HTTPException(
                status_code=404,
                detail="Coop record not found"
            )

        # Create a new instance with the updated values, linking to the previous version
        new_coop = model.DBCoops(
            parent_id=existing_coop.id,  # Link to previous version
            user_id=existing_coop.user_id,
            status=coop_update.status,
            total_fowls=coop_update.total_fowls,
            total_dead_fowls=coop_update.total_dead_fowls,
            total_feed=coop_update.total_feed,
            coop_name=existing_coop.coop_name,  # Keep coop_name the same
            egg_count=coop_update.egg_count,
            collection_date=coop_update.collection_date,
            crates_collected=coop_update.crates_collected,
            remainder_eggs=coop_update.remainder_eggs,
            broken_eggs=coop_update.broken_eggs,
            notes=coop_update.notes,
            efficiency=coop_update.efficiency,
            location_id=coop_update.location_id,
        )

        add_coop_update = crud.create_coop(db_coop=new_coop, db=db)

        return add_coop_update
    except CreationError as err:
        raise HTTPException(500, err)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating coop: {str(e)}")



@router.post("/{id}/rollback", response_model=schema.CoopUpdate)
async def rollback_coop(id: int, db: Session = Depends(get_db)):
    try:
        current_version = crud.read_coop_by_id(coop_id=id, db=db)

        if not current_version:
            raise HTTPException(
                status_code=404,
                detail="Current version not found"
            )
        
        if not current_version.parent_id:
            raise HTTPException(
                status_code=400,
                detail="No previous version available for rollback"
            )
        
        # find previous version
        old_version = crud.read_coop_by_version(coop_id=current_version.parent_id, db=db)

        if not old_version:
            raise HTTPException(
                status_code=404,
                detail="Previous version not found"
            )

        # Create a new record with the old data (restoring it)
        restored_coop = model.DBCoops(
            parent_id=old_version.parent_id,  # Keep the link to the version before that
            user_id=old_version.user_id,
            status=old_version.status,
            total_fowls=old_version.total_fowls,
            total_dead_fowls=old_version.total_dead_fowls,
            total_feed=old_version.total_feed,
            coop_name=old_version.coop_name,
            egg_count=old_version.egg_count,
            collection_date=old_version.collection_date,
            crates_collected=old_version.crates_collected,
            remainder_eggs=old_version.remainder_eggs,
            broken_eggs=old_version.broken_eggs,
            notes=old_version.notes,
            efficiency=old_version.efficiency,
        )

        rolled_back = crud.create_coop(db_coop=restored_coop, db=db)

        return rolled_back

    except CreationError as err:
        raise HTTPException(500, err)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rolling back coop: {str(e)}")


@router.get("/location/{location_id}", response_model=List[schema.CoopOutput])
async def get_coops_by_location(location_id: int, db=Depends(get_db)):
    try:
        coop = crud.read_coops_by_location(location_id, db)
        if not coop:
            raise HTTPException(status_code=404, detail="No coop found for this location")
        return coop
    except NotFoundError:
        raise HTTPException(status_code=404, detail="Coop with this location does not exist")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving coop: {str(e)}")
