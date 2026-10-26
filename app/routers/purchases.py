from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import Material, OrderSeq, PurchaseItem, PurchaseOrder, Supplier, User
from ..schemas import PurchaseIn, PurchaseItemOut, PurchaseOut

router = APIRouter(prefix="/api/purchases", tags=["purchases"], dependencies=[Depends(get_current_user)])


def next_order_no(db: Session, prefix: str, date_val) -> str:
    """生成工单号 PREFIX_YYYYMMDDNNN，事务内调用"""
    date_str = date_val.strftime("%Y%m%d") if isinstance(date_val, datetime) else str(date_val).replace("-", "")[:8]
    seq_row = db.get(OrderSeq, date_str)
    if seq_row is None:
        seq_row = OrderSeq(date_str=date_str, seq=0)
        db.add(seq_row)
        db.flush()
    seq_row.seq += 1
    return f"{prefix}_{date_str}{seq_row.seq:03d}"


def _item_out(it: PurchaseItem) -> PurchaseItemOut:
    return PurchaseItemOut(
        id=it.id,
        material_id=it.material_id,
        material_code=it.material.code,
        material_name=it.material.name,
        spec=it.spec,
        purchase_qty=float(it.purchase_qty),
        claimed_qty=float(it.claimed_qty),
        return_qty=float(it.return_qty),
        remaining_qty=it.remaining_qty,
        remark=it.remark,
    )


def _out(p: PurchaseOrder) -> PurchaseOut:
    return PurchaseOut(
        id=p.id,
        order_no=p.order_no,
        supplier_id=p.supplier_id,
        supplier_name=p.supplier.name if p.supplier else "",
        purchaser=p.purchaser,
        status=p.status,
        purchase_date=p.purchase_date,
        in_stock_date=p.in_stock_date,
        remark=p.remark,
        items=[_item_out(it) for it in p.items],
    )


@router.get("", response_model=list[PurchaseOut])
def list_purchases(keyword: str = "", db: Session = Depends(get_db)):
    q = db.query(PurchaseOrder)
    if keyword:
        like = f"%{keyword}%"
        q = q.outerjoin(Supplier).filter(
            (PurchaseOrder.order_no.like(like))
            | (Supplier.name.like(like))
            | PurchaseOrder.id.in_(
                db.query(PurchaseItem.purchase_order_id).join(Material).filter(
                    (Material.code.like(like)) | (Material.name.like(like))
                )
            )
        )
    rows = q.order_by(PurchaseOrder.in_stock_date.desc(), PurchaseOrder.id.desc()).limit(500).all()
    return [_out(p) for p in rows]


@router.post("", response_model=PurchaseOut)
def create_purchase(body: PurchaseIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if body.supplier_id is not None and db.get(Supplier, body.supplier_id) is None:
        raise HTTPException(404, "供应商不存在")
    for it in body.items:
        if db.get(Material, it.material_id) is None:
            raise HTTPException(404, f"物料 {it.material_id} 不存在")
        if it.purchase_qty <= 0:
            raise HTTPException(400, "采购数量必须大于0")

    p = PurchaseOrder(
        order_no=next_order_no(db, "CG", body.purchase_date),
        supplier_id=body.supplier_id,
        purchaser=body.purchaser,
        status="pending",
        purchase_date=body.purchase_date,
        in_stock_date=body.in_stock_date,
        remark=body.remark,
        created_by=user.id,
    )
    db.add(p)
    db.flush()

    for it in body.items:
        material = db.get(Material, it.material_id)
        db.add(PurchaseItem(
            purchase_order_id=p.id,
            material_id=it.material_id,
            spec=material.spec,
            purchase_qty=it.purchase_qty,
            remark=it.remark,
        ))

    db.commit()
    db.refresh(p)
    return _out(p)


def _replace_items(db: Session, p: PurchaseOrder, items):
    """修改采购单明细：全删全建（仅待审核单，未入过库存账，无扣减记录）"""
    p.items = []
    db.flush()
    for it in items:
        material = db.get(Material, it.material_id)
        db.add(PurchaseItem(
            purchase_order_id=p.id,
            material_id=it.material_id,
            spec=material.spec,
            purchase_qty=it.purchase_qty,
            remark=it.remark,
        ))


@router.put("/{order_id}", response_model=PurchaseOut)
def update_purchase(order_id: int, body: PurchaseIn, db: Session = Depends(get_db)):
    """修改采购单：仅待审核状态可修改（复用添加接口的入参结构）"""
    p = db.get(PurchaseOrder, order_id)
    if p is None:
        raise HTTPException(404, "采购单不存在")
    if p.status == "approved":
        raise HTTPException(400, "已审核的采购单不能修改")
    if body.supplier_id is not None and db.get(Supplier, body.supplier_id) is None:
        raise HTTPException(404, "供应商不存在")
    for it in body.items:
        if db.get(Material, it.material_id) is None:
            raise HTTPException(404, f"物料 {it.material_id} 不存在")
        if it.purchase_qty <= 0:
            raise HTTPException(400, "采购数量必须大于0")
    p.supplier_id = body.supplier_id
    p.purchaser = body.purchaser
    p.purchase_date = body.purchase_date
    p.in_stock_date = body.in_stock_date
    p.remark = body.remark
    _replace_items(db, p, body.items)
    db.commit()
    db.refresh(p)
    return _out(p)


@router.post("/{order_id}/approve", response_model=PurchaseOut)
def approve_purchase(order_id: int, db: Session = Depends(get_db)):
    """审核通过：通过后该单才计入库存，出库/退料才能扣减到它的明细"""
    p = db.get(PurchaseOrder, order_id)
    if p is None:
        raise HTTPException(404, "采购单不存在")
    if p.status == "approved":
        raise HTTPException(400, "采购单已审核")
    # 负数结转：审核瞬间按入库顺序对同物料前置欠账行做结转
    for item in p.items:
        _carry_negative_forward(db, item.material_id, item)
    p.status = "approved"
    db.commit()
    db.refresh(p)
    return _out(p)


@router.get("/by-material/{material_id}")
def purchases_by_material(material_id: int, db: Session = Depends(get_db)):
    """产品库存-详情：该物料剩余不为 0 的采购明细行（含负数欠账行），按入库日期从老到新"""
    if db.get(Material, material_id) is None:
        raise HTTPException(404, "物料不存在")
    rows = (
        db.query(PurchaseItem)
        .join(PurchaseOrder, PurchaseItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseItem.material_id == material_id, PurchaseOrder.status == "approved")
        .order_by(PurchaseOrder.in_stock_date, PurchaseItem.id)
        .all()
    )
    return [
        {
            "order_no": it.order.order_no,
            "supplier_name": it.order.supplier.name if it.order.supplier else "",
            "purchase_date": str(it.order.purchase_date),
            "in_stock_date": str(it.order.in_stock_date),
            "spec": it.spec,
            "purchase_qty": float(it.purchase_qty),
            "claimed_qty": float(it.claimed_qty),
            "return_qty": float(it.return_qty),
            "remaining_qty": round(it.remaining_qty, 2),
        }
        for it in rows
        if round(it.remaining_qty, 2) != 0
    ]


def _carry_negative_forward(db: Session, material_id: int, new_item: PurchaseItem):
    """负数结转：新建采购明细行时，若上一笔明细行剩余为负且整体库存为负，
    把上一笔负数绝对值转为新行的预扣申领量，并将上一笔剩余归零。"""
    prev = (
        db.query(PurchaseItem)
        .join(PurchaseOrder, PurchaseItem.purchase_order_id == PurchaseOrder.id)
        .filter(PurchaseItem.material_id == material_id, PurchaseItem.id != new_item.id)
        .order_by(PurchaseOrder.in_stock_date.desc(), PurchaseItem.id.desc())
        .first()
    )
    if prev is None:
        return
    prev_remaining = prev.remaining_qty
    if prev_remaining < 0:
        # 上一笔被扣穿成负数 → 归零，欠账绝对值转入新行作为预扣申领量
        new_item.claimed_qty = abs(prev_remaining)
        prev.claimed_qty = float(prev.purchase_qty) + float(prev.return_qty)
