from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


# ─────────────────────────────────────────────
# PAYMENT ALLOCATION
# ─────────────────────────────────────────────

class PaymentAllocationCreate(BaseModel):
    document_id: UUID
    amount_allocated: Decimal = Field(..., example=5000.00)

class PaymentAllocationOut(BaseModel):
    id: UUID
    payment_id: UUID
    document_id: UUID
    amount_allocated: Decimal
    allocated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# PAYMENT
# ─────────────────────────────────────────────

class PaymentCreate(BaseModel):
    client_id: Optional[UUID] = None
    reference: str = Field(..., example="PAY-2026-001")
    method: str = Field("bank_transfer", example="bank_transfer")
    amount: Decimal = Field(..., example=10000.00)
    currency: str = Field("MAD", example="MAD")
    exchange_rate: Decimal = Field(1.0, example=1.0)
    bank_reference: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_bank: Optional[str] = None
    notes: Optional[str] = None
    payment_date: date = Field(..., example="2026-05-01")
    allocations: Optional[List[PaymentAllocationCreate]] = []

class PaymentUpdate(BaseModel):
    client_id: Optional[UUID] = None
    method: Optional[str] = None
    amount: Optional[Decimal] = None
    currency: Optional[str] = None
    exchange_rate: Optional[Decimal] = None
    bank_reference: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_bank: Optional[str] = None
    notes: Optional[str] = None
    payment_date: Optional[date] = None
    status: Optional[str] = None

class PaymentOut(BaseModel):
    id: UUID
    enterprise_id: UUID
    client_id: Optional[UUID] = None
    reference: str
    method: str
    amount: Decimal
    currency: str
    exchange_rate: Decimal
    amount_allocated: Decimal
    amount_remaining: Decimal
    bank_reference: Optional[str] = None
    cheque_number: Optional[str] = None
    cheque_bank: Optional[str] = None
    notes: Optional[str] = None
    status: str
    payment_date: date
    allocations: List[PaymentAllocationOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
