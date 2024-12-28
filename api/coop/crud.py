from api.auth import model
from api.coop import schema
from sqlalchemy.orm import Session


class NotFoundError(Exception):
    pass


class CreationError(Exception):
    pass


def read_coops(db):
    return db.query(model.DBCoops).all()


def read_coop_by_id(coop_id: int, db):
    return db.query(model.DBCoops).filter(model.DBCoops.id == coop_id).first()


def read_coop_by_coop_name(coop_name: str, db):
    coop = db.query(model.DBCoops).filter(model.DBCoops.coop_name == coop_name).first()
    if coop is None:
        raise NotFoundError("coop not found")

    return db.query(model.DBCoops).filter(model.DBCoops.coop_name == coop_name).first()


def create_coop(db_coop: model.DBCoops, db: Session):
    db.add(db_coop)
    db.commit()
    db.refresh(db_coop)
    return schema.Coop(**db_coop.__dict__)


def update_coop(db_coop: model.DBCoops, db: Session):
    db.commit()
    db.refresh(db_coop)
    return db_coop


def delete_coop(coop_id: int, db: Session):
    db_coop = read_coop_by_id(coop_id, db)
    db.delete(db_coop)
    db.commit()
    return {"message": "coop has been successfully deleted"}


def read_coop_by_user_id(user_id: int, db):
    return (
        db.query(model.DBCoops)
        .filter(model.DBCoops.user_id == user_id, model.DBCoops.status == "active")
        .first()
    )


def find_coop_by_user_id(user_id: int, db):
    coop = db.query(model.DBCoops).filter(model.DBCoops.user_id == user_id).first()
    if coop is None:
        raise NotFoundError("coop not found")

    return db.query(model.DBCoops).filter(model.DBCoops.user_id == user_id).first()


def find_coop_by_id(coop_id: int, db):
    if db.query(model.DBCoops).filter(model.DBCoops.id == coop_id).first is None:
        raise NotFoundError("Coop not found")
    
    return db.query(model.DBCoops).filter(model.DBCoops.id == coop_id).first()