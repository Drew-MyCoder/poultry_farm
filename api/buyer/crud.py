from api.auth import model
from sqlalchemy.orm import Session


class NotFoundError(Exception):
    pass


class CreationError(Exception):
    pass


def read_buyers(db):
    return db.query(model.DBBuyer).all()


def read_buyer_by_id(buyer_id: int, db):
    return db.query(model.DBBuyer).filter(model.DBBuyer.id == buyer_id).first()


def create_buyer(db_buyer: model.DBBuyer, db):
    db.add(db_buyer)
    db.commit()
    db.refresh(db_buyer)
    return db_buyer


def update_buyer(db_buyer: model.DBBuyer, db: Session):
    db.commit()
    db.refresh(db_buyer)
    return db_buyer


def delete_buyer(buyer_id: int, db: Session):
    db_buyer = read_buyer_by_id(buyer_id, db)
    db.delete(db_buyer)
    db.commit()
    return {"message": "buyer has been successfully deleted"}


def read_buyer_by_name(buyer_name: str, db):
    buyer = db.query(model.DBBuyer).filter(model.DBBuyer.name == buyer_name).first()
    if buyer is None:
        raise NotFoundError("buyer not found")

    return db.query(model.DBBuyer).filter(model.DBBuyer.name == buyer_name).first()



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