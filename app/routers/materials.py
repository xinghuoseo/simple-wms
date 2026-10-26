from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Material
from ..schemas import MaterialIn, MaterialOut

router = APIRouter(prefix="/api/materials", tags=["materials"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[MaterialOut])
def list_materials(keyword: str = "", db: Session = Depends(get_db)):
    q = db.query(Material)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(Material.code.like(like), Material.name.like(like)))
    return q.order_by(Material.code).limit(200).all()


@router.post("", response_model=MaterialOut)
def create_material(body: MaterialIn, db: Session = Depends(get_db)):
    if db.query(Material).filter(Material.code == body.code).first():
        raise HTTPException(400, "物料编号已存在")
    m = Material(**body.model_dump())
    db.add(m)
    db.commit()
    db.refresh(m)
    return m


@router.put("/{material_id}", response_model=MaterialOut)
def update_material(material_id: int, body: MaterialIn, db: Session = Depends(get_db)):
    m = db.get(Material, material_id)
    if m is None:
        raise HTTPException(404, "物料不存在")
    if body.code != m.code and db.query(Material).filter(Material.code == body.code).first():
        raise HTTPException(400, "新物料编号已存在")
    # 物料被采购单/出库单/退料单通过外键关联，修改后所有单据同步生效
    m.code = body.code
    m.name = body.name
    m.spec = body.spec
    m.remark = body.remark
    db.commit()
    db.refresh(m)
    return m
