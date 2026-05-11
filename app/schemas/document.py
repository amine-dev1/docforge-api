from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from decimal import Decimal


# ─────────────────────────────────────────────
# DOCUMENT LINE
# ─────────────────────────────────────────────

class DocumentLineCreate(BaseModel):
    product_id: Optional[UUID] = None
    tax_rate_id: Optional[UUID] = None
    position: int = 0
    type: str = Field("product", example="product")
    reference: Optional[str] = None
    description: str = Field(..., example="Ordinateur portable Dell XPS")
    quantity: Decimal = Field(1, example=2)
    unit: Optional[str] = Field(None, example="pcs")
    unit_price_ht: Decimal = Field(0, example=7500.00)
    discount_pct: Decimal = Field(0, example=5.00)
    discount_amount: Decimal = Field(0, example=0.00)
    tax_rate_value: Decimal = Field(0, example=20.00)

class DocumentLineOut(BaseModel):
    id: UUID
    document_id: UUID
    product_id: Optional[UUID] = None
    tax_rate_id: Optional[UUID] = None
    position: int
    type: str
    reference: Optional[str] = None
    description: str
    quantity: Decimal
    unit: Optional[str] = None
    unit_price_ht: Decimal
    discount_pct: Decimal
    discount_amount: Decimal
    line_total_ht: Decimal
    tax_rate_value: Decimal
    tax_amount: Decimal
    line_total_ttc: Decimal

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# DOCUMENT
# ─────────────────────────────────────────────

class DocumentCreate(BaseModel):
    type: str = Field(..., description="Document type", example="invoice")
    client_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    parent_doc_id: Optional[UUID] = None
    language: str = Field("fr", example="fr")
    currency: str = Field("MAD", example="MAD")
    exchange_rate: Decimal = Field(1.0)
    notes: Optional[str] = None
    terms: Optional[str] = None
    footer: Optional[str] = None
    internal_notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    lines: Optional[List[DocumentLineCreate]] = []

class DocumentUpdate(BaseModel):
    status: Optional[str] = None
    language: Optional[str] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    client_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    notes: Optional[str] = None
    terms: Optional[str] = None
    footer: Optional[str] = None
    internal_notes: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None

class DocumentOut(BaseModel):
    id: UUID
    enterprise_id: UUID
    type: str
    number: str
    status: str
    language: str
    currency: str
    exchange_rate: Decimal
    client_id: Optional[UUID] = None
    supplier_id: Optional[UUID] = None
    parent_doc_id: Optional[UUID] = None
    subtotal_ht: Decimal
    total_discount: Decimal
    total_tax: Decimal
    total_ttc: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    notes: Optional[str] = None
    terms: Optional[str] = None
    footer: Optional[str] = None
    pdf_url: Optional[str] = None
    issued_at: Optional[datetime] = None
    due_at: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    lines: List[DocumentLineOut] = []

    class Config:
        from_attributes = True
