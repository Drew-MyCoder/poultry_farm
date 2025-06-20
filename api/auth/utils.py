from fastapi import HTTPException
from api.auth import (
    model
)
from api.buyer import (
    crud as buyer_crud
)
from api.user import (
    crud as user_crud
) 


def admin_status(user_id: model.DBUser, db):
    try:
        is_admin = user_crud.read_role(user_id=user_id, db=db)
        if is_admin:
            if is_admin.status == 'inactive':
                raise HTTPException('admin is inactive')
            elif is_admin.status == 'suspended':
                raise HTTPException('admin is currently suspended')
            elif is_admin.role != 'admin':
                raise HTTPException('this function can only be performed by an admin')
        else:
            raise buyer_crud.NotFoundError(
                'no admin found'
            )
            print(is_admin.user_id, '<<<<this is admin id')

    except buyer_crud.NotFoundError as err:
        (
            404,
            'sorry cant perform action', err
        )