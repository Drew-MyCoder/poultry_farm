from api.auth import model
from api.coop import schema
from sqlalchemy.orm import Session


class NotFoundError(Exception):
    pass


class CreationError(Exception):
    pass


def read_coops(db):
    return db.query(model.DBCoops).all()


def read_coop_by_id(coop_id: int, db: Session):
    return db.query(model.DBCoops).filter(model.DBCoops.id == coop_id).first()


def read_coop_by_coop_name(coop_name: str, db):
    coop = db.query(model.DBCoops).filter(model.DBCoops.coop_name == coop_name).order_by(model.DBCoops.created_at.desc()).all()
    if coop is None:
        raise NotFoundError("coops not found")

    return coop


def read_coop_by_version(coop_id: int, db):
    return db.query(model.DBCoops).filter(model.DBCoops.id == coop_id).first()


def read_coops_by_location(location_id: int, db: Session):
    return db.query(model.DBCoops).filter(model.DBCoops.location_id == location_id).all()


def create_coop(db_coop: model.DBCoops, db):
    db.add(db_coop)
    db.commit()
    db.refresh(db_coop)
    return db_coop


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

    return coop


def find_coop_by_id(coop_id: int, db):
    coop = db.query(model.DBCoops).filter(model.DBCoops.id == coop_id).first()
    if coop is None:
        raise NotFoundError("Coop not found")
    
    return coop