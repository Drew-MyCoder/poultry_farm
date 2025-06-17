from api.auth import model
from sqlalchemy.orm import Session


class NotFoundError(Exception):
    pass


class CreationError(Exception):
    pass


def read_buyers(db):
    return db.query(model.DBBuyer).all() 


def read_buyer_by_id(buyer_id: int, db: Session):
    return db.query(model.DBBuyer).filter(model.DBBuyer.id == buyer_id).first()


def create_buyer(db_buyer: model.DBBuyer, db):
    try:
        db.add(db_buyer)
        db.commit()
        db.refresh(db_buyer)
        return db_buyer
    except Exception as e:
        db.rollback()
        raise CreationError(f"Failed to create buyer: {str(e)}")


def find_buyer_by_id(buyer_id: int, db):
    # if db.query(model.DBBuyer).filter(model.DBBuyer.id == buyer_id) is None:
    #     raise NotFoundError('Buyer not found')

    # return db.query(model.DBBuyer).filter(model.DBBuyer.id == buyer_id)
    buyer = db.query(model.DBBuyer).filter(model.DBBuyer.id == buyer_id).first()
    if buyer is None:
        raise NotFoundError("Buyer not found")
    return buyer


def read_buyer_by_location(location_id: int, db: Session):
    return db.query(model.DBBuyer).filter(model.DBBuyer.location_id == location_id).all()


# def update_buyer(db: Session, buyer_id: int, updated_data: dict):
#     buyer = db.query(model.DBBuyer).filter(model.DBBuyer.id == buyer_id).first()
    
#     if not buyer:
#         return None  # Or raise an exception if the buyer doesn't exist
#     print('received updated data', updated_data)
#     for key, value in updated_data.items():
#         if value is not None and value != 0:
#             print(f'updating {key} to {value}')
#             setattr(buyer, key, value)

#     db.commit()
#     db.refresh(buyer)  # Ensure it's a model instance before refreshing
#     return buyer

def update_buyer(db_buyer: model.DBBuyer, db: Session):
    try:
        db.commit()
        db.refresh(db_buyer)
        return db_buyer
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to update buyer: {str(e)}")



# def delete_buyer(buyer_id: int, db: Session):
#     db_buyer = read_buyer_by_id(buyer_id, db)
#     db.delete(db_buyer)
#     db.commit()
#     return {"message": "buyer has been successfully deleted"}

def delete_buyer(buyer_id: int, db: Session):
    db_buyer = read_buyer_by_id(buyer_id, db)
    if db_buyer is None:
        raise NotFoundError("Buyer not found")
    
    try:
        db.delete(db_buyer)
        db.commit()
        return {"message": "Buyer has been successfully deleted"}
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to delete buyer: {str(e)}")


def read_buyer_by_name(buyer_name: str, db):
    buyer = db.query(model.DBBuyer).filter(model.DBBuyer.name == buyer_name).all()
    if buyer is None:
        raise NotFoundError("buyer not found")

    return buyer



# def read_coop_by_user_id(user_id: int, db):
#     return (
#         db.query(model.DBBuyer)
#         .filter(model.DBBuyer.user_id == user_id, model.DBBuyer.status == "active")
#         .first()
#     )


# def find_coop_by_user_id(user_id: int, db):
#     coop = db.query(model.DBBuyer).filter(model.DBBuyer.user_id == user_id).first()
#     if coop is None:
#         raise NotFoundError("coop not found")

#     return db.query(model.DBBuyer).filter(model.DBBuyer.user_id == user_id).first()


# def find_coop_by_id(coop_id: int, db):
#     if db.query(model.DBBuyer).filter(model.DBBuyer.id == coop_id).first is None:
#         raise NotFoundError("Coop not found")
    
#     return db.query(model.DBBuyer).filter(model.DBBuyer.id == coop_id).first()