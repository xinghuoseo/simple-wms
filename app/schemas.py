from datetime import date, datetime

from pydantic import BaseModel, Field


# ---------- 认证 ----------
class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    real_name: str

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    token: str
    user: UserOut


# ---------- 用户 ----------
class UserIn(BaseModel):
    username: str
    password: str
    real_name: str = ""


class UserUpdateIn(BaseModel):
    password: str | None = None
    real_name: str | None = None


# ---------- 物料 ----------
class MaterialIn(BaseModel):
    code: str
    name: str
    spec: str = ""
    remark: str = ""


class MaterialOut(BaseModel):
    id: int
    code: str
    name: str
    spec: str
    remark: str = ""

    class Config:
        from_attributes = True


# ---------- 供应商 ----------
class SupplierIn(BaseModel):
    name: str
    contact: str = ""
    phone: str = ""
    remark: str = ""


class SupplierOut(SupplierIn):
    id: int

    class Config:
        from_attributes = True


# ---------- 采购 ----------
class PurchaseItemIn(BaseModel):
    material_id: int
    purchase_qty: float
    remark: str = ""


class PurchaseItemOut(BaseModel):
    id: int
    material_id: int
    material_code: str = ""
    material_name: str = ""
    spec: str = ""
    purchase_qty: float
    claimed_qty: float
    return_qty: float
    remaining_qty: float
    remark: str = ""


class PurchaseIn(BaseModel):
    supplier_id: int | None = None
    purchaser: str = ""
    purchase_date: date
    in_stock_date: date
    remark: str = ""
    items: list[PurchaseItemIn] = Field(min_length=1)


class PurchaseOut(BaseModel):
    id: int
    order_no: str
    supplier_id: int | None = None
    supplier_name: str = ""
    purchaser: str = ""
    status: str = "pending"
    purchase_date: date
    in_stock_date: date
    remark: str
    items: list[PurchaseItemOut] = []


# ---------- 出库 ----------
class IssueItemIn(BaseModel):
    material_id: int
    qty: float
    remark: str = ""


class IssueItemOut(BaseModel):
    id: int
    material_id: int
    material_code: str = ""
    material_name: str = ""
    spec: str = ""
    qty: float
    return_qty: float
    remark: str = ""


class IssueIn(BaseModel):
    issuer: str
    issue_date: date
    issue_type: str = "生产申领"
    remark: str = ""
    items: list[IssueItemIn] = Field(min_length=1)


class IssueOut(BaseModel):
    id: int
    order_no: str
    issuer: str
    issue_type: str = "生产申领"
    status: str = "pending"
    issue_date: date
    remark: str
    return_qty: float = 0
    items: list[IssueItemOut] = []
    created_at: datetime


# ---------- 退回 ----------
class ReturnItemIn(BaseModel):
    issue_item_id: int
    qty: float
    remark: str = ""


class ReturnIn(BaseModel):
    issue_order_no: str
    return_date: date
    remark: str = ""
    items: list[ReturnItemIn] = Field(min_length=1)


class ReturnItemOut(BaseModel):
    id: int
    issue_item_id: int
    material_code: str = ""
    material_name: str = ""
    qty: float
    remark: str = ""


class ReturnOut(BaseModel):
    id: int
    return_no: str
    issue_order_no: str
    return_date: date
    remark: str = ""
    items: list[ReturnItemOut] = []


# ---------- 库存 ----------
class InventoryOut(BaseModel):
    material_id: int
    material_code: str
    material_name: str
    spec: str
    remark: str = ""
    stock_qty: float
    purchase_total: float
    issue_total: float
    return_total: float
