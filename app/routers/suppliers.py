from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Supplier
from ..schemas import SupplierIn, SupplierOut

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[SupplierOut])
def list_suppliers(db: Session = Depends(get_db)):
    return db.query(Supplier).order_by(Supplier.id.desc()).all()


@router.post("", response_model=SupplierOut)
def create_supplier(body: SupplierIn, db: Session = Depends(get_db)):
    s = Supplier(**body.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


@router.put("/{sid}", response_model=SupplierOut)
def update_supplier(sid: int, body: SupplierIn, db: Session = Depends(get_db)):
    s = db.get(Supplier, sid)
    if s is None:
        raise HTTPException(404, "供应商不存在")
    for k, v in body.model_dump().items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return s


@router.delete("/{sid}")
def delete_supplier(sid: int, db: Session = Depends(get_db)):
    s = db.get(Supplier, sid)
    if s is None:
        raise HTTPException(404, "供应商不存在")
    db.delete(s)
    db.commit()
    return {"ok": True}
