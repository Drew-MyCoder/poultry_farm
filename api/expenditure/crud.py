from api.auth import model
from sqlalchemy.orm import Session


class NotFoundError(Exception):
    pass


class CreationError(Exception):
    pass


def read_expenditures(db):
    return db.query(model.DBExpenditure).all()


def read_expenditure_by_id(expenditure_id: int, db):
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.id == expenditure_id).first()


def create_expenditure(db_expenditure: model.DBExpenditure, db):
    db.add(db_expenditure)
    db.commit()
    db.refresh(db_expenditure)
    return db_expenditure


def update_expenditure(db_expenditure: model.DBExpenditure, db: Session):
    db.commit()
    db.refresh(db_expenditure)
    return db_expenditure


def delete_expenditure(expenditure_id: int, db: Session):
    db_expenditure = read_expenditure_by_id(expenditure_id, db)
    db.delete(db_expenditure)
    db.commit()
    return {"message": "expenditure has been successfully deleted"}


def read_expenditure_by_name(expenditure_name: str, db):
    expenditure = db.query(model.DBExpenditure).filter(model.DBExpenditure.reference == expenditure_name).first()
    if expenditure is None:
        raise NotFoundError("expenditure not found")

    return db.query(model.DBExpenditure).filter(model.DBExpenditure.reference == expenditure_name).first()


def find_expenditure_by_id(expenditure_id: int, db):
    if db.query(model.DBExpenditure).filter(model.DBExpenditure.id == expenditure_id).first is None:
        raise NotFoundError("expenditure not found")
    
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.id == expenditure_id).first()