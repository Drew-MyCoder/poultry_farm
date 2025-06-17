from api.auth import model
from sqlalchemy.orm import Session


class NotFoundError(Exception):
    pass


class CreationError(Exception):
    pass


def read_expenditures(db: Session):
    return db.query(model.DBExpenditure).all()


def read_expenditure_by_id(expenditure_id: int, db: Session):
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.id == expenditure_id).first()


def create_expenditure(db_expenditure: model.DBExpenditure, db: Session):
    try:
        db.add(db_expenditure)
        db.commit()
        db.refresh(db_expenditure)
        return db_expenditure
    except Exception as e:
        db.rollback()
        raise CreationError(f"Failed to create expenditure: {str(e)}")


def update_expenditure(db_expenditure: model.DBExpenditure, db: Session):
    try:
        db.commit()
        db.refresh(db_expenditure)
        return db_expenditure
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to update expenditure: {str(e)}")


def delete_expenditure(expenditure_id: int, db: Session):
    db_expenditure = read_expenditure_by_id(expenditure_id, db)
    if db_expenditure is None:
        raise NotFoundError("Expenditure not found")
    
    try:
        db.delete(db_expenditure)
        db.commit()
        return {"message": "Expenditure has been successfully deleted"}
    except Exception as e:
        db.rollback()
        raise Exception(f"Failed to delete expenditure: {str(e)}")


def read_expenditure_by_reference(reference: str, db: Session):
    expenditure = db.query(model.DBExpenditure).filter(model.DBExpenditure.reference == reference).first()
    if expenditure is None:
        raise NotFoundError("Expenditure not found")
    return expenditure


def find_expenditure_by_id(expenditure_id: int, db: Session):
    expenditure = db.query(model.DBExpenditure).filter(model.DBExpenditure.id == expenditure_id).first()
    if expenditure is None:
        raise NotFoundError("Expenditure not found")
    return expenditure


def read_expenditures_by_location(location_id: int, db: Session):
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.location_id == location_id).all()


def read_expenditures_by_user(user_id: int, db: Session):
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.user_id == user_id).all()


def read_expenditures_by_category(category: str, db: Session):
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.category == category).all()


def read_expenditures_by_status(status: str, db: Session):
    return db.query(model.DBExpenditure).filter(model.DBExpenditure.status == status).all()