from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..database import get_db
from ..models import (
    IssueItem, IssueOrder, Material, PurchaseItem, PurchaseOrder, ReturnItem, ReturnOrder, User,
)
from .purchases import next_order_no
from ..schemas import (
    InventoryOut, IssueIn, IssueItemOut, IssueOut, ReturnIn, ReturnItemOut, ReturnOut,
)

router = APIRouter(prefix="/api", tags=["issues"], dependencies=[Depends(get_current_user)])


# ---------------- 出库 ----------------

def _issue_item_out(it: IssueItem) -> IssueItemOut:
    return IssueItemOut(
        id=it.id,
        material_id=it.material_id,
        material_code=it.material.code,
        material_name=it.material.name,
        spec=it.material.spec,
        qty=float(it.qty),
        return_qty=float(it.return_qty),
        remark=it.remark,
    )


def _issue_out(i: IssueOrder) -> IssueOut:
    return IssueOut(
        id=i.id,
        order_no=i.order_no,
        issuer=i.issuer,
        issue_type=i.issue_type or "生产申领",
        status=i.status or "approved",
        issue_date=i.issue_date,
        remark=i.remark,
        return_qty=float(sum(it.return_qty for it in i.items)),
        items=[_issue_item_out(it) for it in i.items],
        created_at=i.created_at,
    )


@router.get("/issues", response_model=list[IssueOut])
def list_issues(keyword: str = "", db: Session = Depends(get_db)):
    q = db.query(IssueOrder)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (IssueOrder.order_no.like(like))
            | (IssueOrder.issuer.like(like))
            | IssueOrder.id.in_(
                db.query(IssueItem.issue_order_id).join(Material).filter(
                    (Material.code.like(like)) | (Material.name.like(like))
                )
            )
        )
    rows = q.order_by(IssueOrder.id.desc()).limit(500).all()
    return [_issue_out(i) for i in rows]


@router.post("/issues", response_model=IssueOut)
def create_issue(body: IssueIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """创建出库单：仅登记，不扣库存；审核通过后才 FIFO 扣减"""
    for it in body.items:
        if db.get(Material, it.material_id) is None:
            raise HTTPException(404, f"物料 {it.material_id} 不存在")
        if it.qty <= 0:
            raise HTTPException(400, "领料数量必须大于0")

    prefix = "FQ" if body.issue_type == "非工单申领" else "CK"
    issue = IssueOrder(
        order_no=next_order_no(db, prefix, body.issue_date),
        issuer=body.issuer,
        issue_type=body.issue_type,
        status="pending",
        issue_date=body.issue_date,
        remark=body.remark,
        created_by=user.id,
    )
    db.add(issue)
    db.flush()

    for it in body.items:
        db.add(IssueItem(issue_order_id=issue.id, material_id=it.material_id, qty=it.qty, remark=it.remark))

    db.commit()
    db.refresh(issue)
    return _issue_out(issue)


def _deduct_fifo(db: Session, issue: IssueOrder):
    """FIFO 扣减：该物料按入库日期从老到新（仅已审核采购单），不足时最后一笔扣成负数欠账"""
    for it in issue.items:
        purchases = (
            db.query(PurchaseItem)
            .join(PurchaseOrder)
            .filter(PurchaseItem.material_id == it.material_id, PurchaseOrder.status == "approved")
            .order_by(PurchaseOrder.in_stock_date, PurchaseOrder.id)
            .with_for_update()
            .all()
        )
        if not purchases:
            raise HTTPException(400, f"物料 {it.material.code} 没有已审核的采购单，无法审核出库")

        remaining = float(it.qty)
        for p in purchases:
            if remaining <= 0:
                break
            avail = float(p.purchase_qty) - float(p.claimed_qty) + float(p.return_qty)
            if avail > 0:
                take = min(avail, remaining)
                p.claimed_qty = float(p.claimed_qty) + take
                remaining -= take
        if remaining > 0:
            # 各行剩余都不足 → 最后一笔（最新入库）扣成负数，表示欠账
            last = purchases[-1]
            last.claimed_qty = float(last.claimed_qty) + remaining


@router.post("/issues/{order_id}/approve", response_model=IssueOut)
def approve_issue(order_id: int, db: Session = Depends(get_db)):
    """审核通过：通过后 FIFO 扣减库存"""
    issue = db.get(IssueOrder, order_id)
    if issue is None:
        raise HTTPException(404, "出库单不存在")
    if issue.status == "approved":
        raise HTTPException(400, "出库单已审核")
    _deduct_fifo(db, issue)
    issue.status = "approved"
    db.commit()
    db.refresh(issue)
    return _issue_out(issue)


@router.delete("/issues/{order_id}")
def delete_issue(order_id: int, db: Session = Depends(get_db)):
    """删除出库单：仅待审核可删（未扣库存，直接删）；已审核单如有退料先冲销回补，再反向回补采购行"""
    issue = db.get(IssueOrder, order_id)
    if issue is None:
        raise HTTPException(404, "出库单不存在")
    if issue.status == "approved":
        # 有退料记录的已审核单不允许删（退料链复杂，需先删退料单）
        has_return = db.query(ReturnItem).filter(
            ReturnItem.issue_item_id.in_([it.id for it in issue.items] or [0])
        ).first() is not None
        if has_return:
            raise HTTPException(400, "该出库单已有退料记录，请先删除对应退料单")
        # 反向回补：按出库时扣减的量，从新到老回补采购行 claimed_qty
        for it in issue.items:
            purchases = (
                db.query(PurchaseItem)
                .join(PurchaseOrder)
                .filter(PurchaseItem.material_id == it.material_id, PurchaseOrder.status == "approved")
                .order_by(PurchaseOrder.in_stock_date.desc(), PurchaseOrder.id.desc())
                .with_for_update()
                .all()
            )
            remaining = float(it.qty)
            for p in purchases:
                if remaining <= 0:
                    break
                occupied = float(p.claimed_qty) - float(p.return_qty)
                if occupied > 0:
                    add = min(occupied, remaining)
                    p.claimed_qty = float(p.claimed_qty) - add
                    remaining -= add
    db.delete(issue)
    db.commit()
    return {"ok": True}


# ---------------- 退回 ----------------

@router.get("/issues/{order_no}/detail-for-return")
def detail_for_return(order_no: str, db: Session = Depends(get_db)):
    """退回弹窗：选定出库单后，返回其全部明细（出库数量锁定，仅可改回退数量）"""
    issue = db.query(IssueOrder).filter(IssueOrder.order_no == order_no).first()
    if issue is None:
        raise HTTPException(404, "出库单不存在")
    return {
        "order_no": issue.order_no,
        "issue_date": issue.issue_date,
        "issuer": issue.issuer,
        "items": [
            {
                "issue_item_id": it.id,
                "material_code": it.material.code,
                "material_name": it.material.name,
                "spec": it.material.spec,
                "qty": float(it.qty),
                "returned": float(it.return_qty),
                "returnable": float(it.qty) - float(it.return_qty),
            }
            for it in issue.items
        ],
    }


@router.get("/returns", response_model=list[ReturnOut])
def list_returns(keyword: str = "", db: Session = Depends(get_db)):
    q = db.query(ReturnOrder)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(
            (ReturnOrder.return_no.like(like))
            | ReturnOrder.issue_order_id.in_(
                db.query(IssueOrder.id).filter(IssueOrder.order_no.like(like))
            )
            | ReturnOrder.id.in_(
                db.query(ReturnItem.return_order_id).join(Material).filter(
                    (Material.code.like(like)) | (Material.name.like(like))
                )
            )
        )
    rows = q.order_by(ReturnOrder.id.desc()).limit(500).all()
    out = []
    for r in rows:
        out.append(ReturnOut(
            id=r.id,
            return_no=r.return_no,
            issue_order_no=r.issue_order.order_no,
            return_date=r.return_date,
            remark=r.remark,
            items=[
                ReturnItemOut(
                    id=it.id,
                    issue_item_id=it.issue_item_id,
                    material_code=it.material.code,
                    material_name=it.material.name,
                    qty=float(it.qty),
                    remark=it.remark,
                )
                for it in r.items
            ],
        ))
    return out


@router.post("/returns", response_model=ReturnOut)
def create_return(body: ReturnIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    issue = db.query(IssueOrder).filter(IssueOrder.order_no == body.issue_order_no).first()
    if issue is None:
        raise HTTPException(404, "出库单不存在")
    if issue.status != "approved":
        raise HTTPException(400, "出库单尚未审核，不能退料")

    issue_items = {it.id: it for it in issue.items}
    remark_map = {it.issue_item_id: it.remark for it in body.items}
    valid = []
    for it in body.items:
        row = issue_items.get(it.issue_item_id)
        if row is None:
            raise HTTPException(400, "退回明细不属于该出库单")
        if it.qty <= 0:
            continue
        if float(row.return_qty) + it.qty > float(row.qty):
            raise HTTPException(400, f"物料 {row.material.name} 回退数量超过可退数量")
        valid.append((row, it.qty))
    if not valid:
        raise HTTPException(400, "回退数量必须大于0")

    ret = ReturnOrder(
        return_no=next_order_no(db, "TL", body.return_date),
        issue_order_id=issue.id,
        return_date=body.return_date,
        remark=body.remark,
        created_by=user.id,
    )
    db.add(ret)
    db.flush()

    for row, qty in valid:
        # 反向回补采购明细：按入库日期从新到老，优先回补被扣穿的最新单（仅已审核单）
        purchases = (
            db.query(PurchaseItem)
            .join(PurchaseOrder)
            .filter(PurchaseItem.material_id == row.material_id, PurchaseOrder.status == "approved")
            .order_by(PurchaseOrder.in_stock_date.desc(), PurchaseOrder.id.desc())
            .with_for_update()
            .all()
        )
        remaining = qty
        for p in purchases:
            if remaining <= 0:
                break
            occupied = float(p.claimed_qty) - float(p.return_qty)
            if occupied > 0:
                add = min(occupied, remaining)
                p.return_qty = float(p.return_qty) + add
                remaining -= add

        db.add(ReturnItem(
            return_order_id=ret.id,
            issue_item_id=row.id,
            material_id=row.material_id,
            qty=qty,
            remark=remark_map.get(row.id, ""),
        ))
        row.return_qty = float(row.return_qty) + qty

    db.commit()
    db.refresh(ret)
    return ReturnOut(
        id=ret.id,
        return_no=ret.return_no,
        issue_order_no=issue.order_no,
        return_date=ret.return_date,
        remark=ret.remark,
        items=[
            ReturnItemOut(
                id=it.id, issue_item_id=it.issue_item_id,
                material_code=it.material.code, material_name=it.material.name,
                qty=float(it.qty),
                remark=it.remark,
            )
            for it in ret.items
        ],
    )


# ---------------- 库存聚合 ----------------

@router.get("/inventory", response_model=list[InventoryOut])
def inventory(keyword: str = "", db: Session = Depends(get_db)):
    q = db.query(Material)
    if keyword:
        like = f"%{keyword}%"
        q = q.filter(or_(Material.code.like(like), Material.name.like(like)))

    stats = (
        db.query(
            PurchaseItem.material_id,
            func.sum(PurchaseItem.purchase_qty).label("purchase_total"),
            func.sum(PurchaseItem.claimed_qty).label("claimed_total"),
            func.sum(PurchaseItem.return_qty).label("return_total"),
        )
        .join(PurchaseOrder)
        .filter(PurchaseOrder.status == "approved")
        .group_by(PurchaseItem.material_id)
        .all()
    )
    stat_map = {s.material_id: s for s in stats}

    result = []
    for m in q.order_by(Material.code).all():
        s = stat_map.get(m.id)
        if s is None:
            continue
        purchase_total = float(s.purchase_total or 0)
        claimed_total = float(s.claimed_total or 0)
        return_total = float(s.return_total or 0)
        result.append(InventoryOut(
            material_id=m.id,
            material_code=m.code,
            material_name=m.name,
            spec=m.spec,
            remark=m.remark,
            stock_qty=purchase_total - claimed_total + return_total,
            purchase_total=purchase_total,
            issue_total=claimed_total,
            return_total=return_total,
        ))
    return result
