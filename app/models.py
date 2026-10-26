from datetime import datetime

from sqlalchemy import (
    DATE, DATETIME, DECIMAL, ForeignKey, Integer, String, UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    real_name: Mapped[str] = mapped_column(String(50), default="")
    created_at: Mapped[datetime] = mapped_column(DATETIME, server_default=func.now())


class Supplier(Base):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100))
    contact: Mapped[str] = mapped_column(String(50), default="")
    phone: Mapped[str] = mapped_column(String(20), default="")
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DATETIME, server_default=func.now())


class Material(Base):
    __tablename__ = "materials"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    spec: Mapped[str] = mapped_column(String(100), default="")
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DATETIME, server_default=func.now())


class PurchaseOrder(Base):
    """采购单（表头）：一张单可含多个供应商？（不，供应商在单上）——一张单对应一个供应商；
    需要多供应商时开多张单。明细在 purchase_items。"""

    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(20), unique=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    purchaser: Mapped[str] = mapped_column(String(50), default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending 待审核 / approved 已审核
    purchase_date: Mapped[str] = mapped_column(DATE)
    in_stock_date: Mapped[str] = mapped_column(DATE)
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, server_default=func.now())

    supplier = relationship("Supplier")
    items = relationship("PurchaseItem", back_populates="order", cascade="all, delete-orphan")


class PurchaseItem(Base):
    """采购明细：FIFO / 负数结转都作用在这一行（一行 = 一个物料一笔入库）"""

    __tablename__ = "purchase_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    spec: Mapped[str] = mapped_column(String(100), default="")
    purchase_qty: Mapped[float] = mapped_column(DECIMAL(12, 2))
    claimed_qty: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)
    return_qty: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)
    remark: Mapped[str] = mapped_column(String(255), default="")

    order = relationship("PurchaseOrder", back_populates="items")
    material = relationship("Material")

    @property
    def remaining_qty(self) -> float:
        return float(self.purchase_qty) - float(self.claimed_qty) + float(self.return_qty)


class IssueOrder(Base):
    """销售/领料出库单（表头）"""

    __tablename__ = "issue_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(20), unique=True)
    issuer: Mapped[str] = mapped_column(String(50), default="")
    issue_type: Mapped[str] = mapped_column(String(20), default="生产申领")  # 生产申领/非工单申领
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending 待审核 / approved 已审核
    issue_date: Mapped[str] = mapped_column(DATE)
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, server_default=func.now())

    items = relationship("IssueItem", back_populates="order", cascade="all, delete-orphan")


class IssueItem(Base):
    """出库明细：一行 = 一个物料的出库量（可跨多张采购单 FIFO 扣减）"""

    __tablename__ = "issue_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    issue_order_id: Mapped[int] = mapped_column(ForeignKey("issue_orders.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    qty: Mapped[float] = mapped_column(DECIMAL(12, 2))
    return_qty: Mapped[float] = mapped_column(DECIMAL(12, 2), default=0)
    remark: Mapped[str] = mapped_column(String(255), default="")

    order = relationship("IssueOrder", back_populates="items")
    material = relationship("Material")


class ReturnOrder(Base):
    """退回单（表头）：只针对一张出库单"""

    __tablename__ = "return_orders"
    __table_args__ = (UniqueConstraint("return_no", name="uq_return_no"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_no: Mapped[str] = mapped_column(String(20))
    issue_order_id: Mapped[int] = mapped_column(ForeignKey("issue_orders.id"))
    return_date: Mapped[str] = mapped_column(DATE)
    remark: Mapped[str] = mapped_column(String(255), default="")
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DATETIME, server_default=func.now())

    issue_order = relationship("IssueOrder")
    items = relationship("ReturnItem", back_populates="order", cascade="all, delete-orphan")


class ReturnItem(Base):
    """退回明细：一行 = 对某出库明细行退多少"""

    __tablename__ = "return_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    return_order_id: Mapped[int] = mapped_column(ForeignKey("return_orders.id"))
    issue_item_id: Mapped[int] = mapped_column(ForeignKey("issue_items.id"))
    material_id: Mapped[int] = mapped_column(ForeignKey("materials.id"))
    qty: Mapped[float] = mapped_column(DECIMAL(12, 2))
    remark: Mapped[str] = mapped_column(String(255), default="")

    order = relationship("ReturnOrder", back_populates="items")
    material = relationship("Material")


class OrderSeq(Base):
    """工单号每日序号"""

    __tablename__ = "order_seq"

    date_str: Mapped[str] = mapped_column(String(8), primary_key=True)
    seq: Mapped[int] = mapped_column(Integer, default=0)
