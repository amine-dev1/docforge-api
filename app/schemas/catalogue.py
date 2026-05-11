from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ─────────────────────────────────────────────
# UNIT OF MEASURE
# ─────────────────────────────────────────────

class UnitOfMeasureCreate(BaseModel):
    name: str = Field(..., example="Kilogramme")
    symbol: str = Field(..., example="kg")
    is_default: bool = False

class UnitOfMeasureUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    is_default: Optional[bool] = None

class UnitOfMeasureOut(BaseModel):
    id: UUID
    enterprise_id: UUID
    name: str
    symbol: str
    is_default: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# TAX RATE
# ─────────────────────────────────────────────

class TaxRateCreate(BaseModel):
    name: str = Field(..., example="TVA 20%")
    label: str = Field(..., example="20%")
    rate: Decimal = Field(..., example=20.00)
    type: str = Field("TVA", example="TVA")
    is_default: bool = False
    is_active: bool = True

class TaxRateUpdate(BaseModel):
    name: Optional[str] = None
    label: Optional[str] = None
    rate: Optional[Decimal] = None
    type: Optional[str] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class TaxRateOut(BaseModel):
    id: UUID
    enterprise_id: UUID
    name: str
    label: str
    rate: Decimal
    type: str
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# PRODUCT CATEGORY
# ─────────────────────────────────────────────

class ProductCategoryCreate(BaseModel):
    parent_id: Optional[UUID] = None
    name: str = Field(..., example="Informatique")
    code: Optional[str] = Field(None, example="INFO")
    description: Optional[str] = None
    sort_order: int = 0

class ProductCategoryUpdate(BaseModel):
    parent_id: Optional[UUID] = None
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None

class ProductCategoryOut(BaseModel):
    id: UUID
    enterprise_id: UUID
    parent_id: Optional[UUID] = None
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    sort_order: int
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# PRODUCT
# ─────────────────────────────────────────────

class ProductCreate(BaseModel):
    category_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    tax_rate_id: Optional[UUID] = None
    code: Optional[str] = Field(None, example="PRD-001")
    reference: Optional[str] = None
    name: str = Field(..., example="Ordinateur portable")
    description: Optional[str] = None
    type: str = Field("product", example="product")
    purchase_price_ht: Decimal = Field(0, example=5000.00)
    sale_price_ht: Decimal = Field(0, example=7500.00)
    is_active: bool = True

class ProductUpdate(BaseModel):
    category_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    tax_rate_id: Optional[UUID] = None
    code: Optional[str] = None
    reference: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    purchase_price_ht: Optional[Decimal] = None
    sale_price_ht: Optional[Decimal] = None
    is_active: Optional[bool] = None

class ProductOut(BaseModel):
    id: UUID
    enterprise_id: UUID
    category_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    tax_rate_id: Optional[UUID] = None
    code: Optional[str] = None
    reference: Optional[str] = None
    name: str
    description: Optional[str] = None
    type: str
    purchase_price_ht: Decimal
    sale_price_ht: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
