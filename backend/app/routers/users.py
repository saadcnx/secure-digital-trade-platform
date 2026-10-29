from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import Address, User
from app.schemas import AddressIn, AddressOut, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def _unset_defaults(db: Session, user_id: int) -> None:
    db.execute(update(Address).where(Address.user_id == user_id).values(is_default=False))


def _own_address(db: Session, user: User, address_id: int) -> Address:
    address = db.get(Address, address_id)
    if not address or address.user_id != user.id:
        raise HTTPException(404, "Address not found")
    return address


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.patch("/me", response_model=UserOut)
def update_me(data: UserUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(user, key, value)
    db.commit()
    return user


@router.get("/me/addresses", response_model=list[AddressOut])
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(select(Address).where(Address.user_id == user.id).order_by(Address.id)).all()


@router.post("/me/addresses", response_model=AddressOut, status_code=201)
def add_address(data: AddressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    values = data.model_dump()
    has_any = db.scalar(select(Address.id).where(Address.user_id == user.id).limit(1)) is not None
    if values["is_default"] or not has_any:
        _unset_defaults(db, user.id)
        values["is_default"] = True
    address = Address(user_id=user.id, **values)
    db.add(address)
    db.commit()
    return address


@router.put("/me/addresses/{address_id}", response_model=AddressOut)
def update_address(
    address_id: int,
    data: AddressIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    address = _own_address(db, user, address_id)
    if data.is_default:
        _unset_defaults(db, user.id)
    for key, value in data.model_dump().items():
        setattr(address, key, value)
    db.commit()
    return address


@router.delete("/me/addresses/{address_id}", status_code=204)
def delete_address(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = _own_address(db, user, address_id)
    db.delete(address)
    db.commit()