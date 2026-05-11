from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from uuid import UUID
from decimal import Decimal

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.models.finance import Payment, PaymentAllocation
from app.models.document import Document
from app.schemas.finance import PaymentCreate, PaymentUpdate, PaymentOut, PaymentAllocationOut
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.get("/", response_model=StandardResponse[List[PaymentOut]])
async def list_payments(
    page: int = 1,
    size: int = 20,
    status_filter: str = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all payments for the authenticated tenant."""
    query = db.query(Payment).filter(Payment.enterprise_id == ctx.enterprise.id)
    if status_filter:
        query = query.filter(Payment.status == status_filter)
    payments = query.order_by(Payment.payment_date.desc()).offset((page - 1) * size).limit(size).all()
    return {"status": 200, "data": payments}


@router.post("/", response_model=StandardResponse[PaymentOut], status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """
    Record a new payment and optionally allocate it to one or more documents.
    The payment reference must be unique.
    """
    existing = db.query(Payment).filter(Payment.reference == payment_in.reference).first()
    if existing:
        raise HTTPException(status_code=400, detail="Payment reference already exists")

    allocations_data = payment_in.allocations or []
    payment_data = payment_in.model_dump(exclude={"allocations"})

    payment = Payment(
        **payment_data,
        enterprise_id=ctx.enterprise.id,
        created_by=ctx.user.id,
        amount_remaining=payment_in.amount,
        status="pending",
    )
    db.add(payment)
    db.flush()

    total_allocated = Decimal(0)
    for alloc in allocations_data:
        doc = db.query(Document).filter(
            Document.id == alloc.document_id,
            Document.enterprise_id == ctx.enterprise.id,
        ).first()
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {alloc.document_id} not found")

        allocation = PaymentAllocation(
            payment_id=payment.id,
            document_id=alloc.document_id,
            amount_allocated=alloc.amount_allocated,
        )
        db.add(allocation)

        # Update document amounts
        doc.amount_paid = (doc.amount_paid or Decimal(0)) + alloc.amount_allocated
        doc.amount_due = doc.total_ttc - doc.amount_paid
        if doc.amount_due <= 0:
            doc.status = "paid"
        elif doc.amount_paid > 0:
            doc.status = "partial"

        total_allocated += alloc.amount_allocated

    payment.amount_allocated = total_allocated
    payment.amount_remaining = payment.amount - total_allocated
    if total_allocated >= payment.amount:
        payment.status = "allocated"
    elif total_allocated > 0:
        payment.status = "partial"
    else:
        payment.status = "pending"

    db.commit()
    db.refresh(payment)
    return {"status": 201, "data": payment}


@router.get("/{payment_id}", response_model=StandardResponse[PaymentOut])
async def get_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Get a single payment with its allocations."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.enterprise_id == ctx.enterprise.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"status": 200, "data": payment}


@router.patch("/{payment_id}", response_model=StandardResponse[PaymentOut])
async def update_payment(
    payment_id: UUID,
    payment_in: PaymentUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Update payment metadata (notes, bank reference, etc.)."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.enterprise_id == ctx.enterprise.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")

    for field, value in payment_in.model_dump(exclude_none=True).items():
        setattr(payment, field, value)

    db.commit()
    db.refresh(payment)
    return {"status": 200, "data": payment}


@router.delete("/{payment_id}", response_model=StandardResponse[dict])
async def delete_payment(
    payment_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """
    Delete a payment and reverse all its document allocations.
    Only allowed for payments in 'pending' status.
    """
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.enterprise_id == ctx.enterprise.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status not in ("pending",):
        raise HTTPException(status_code=400, detail="Only pending payments can be deleted")

    # Reverse allocations
    for alloc in payment.allocations:
        doc = db.query(Document).filter(Document.id == alloc.document_id).first()
        if doc:
            doc.amount_paid = (doc.amount_paid or Decimal(0)) - alloc.amount_allocated
            doc.amount_due = doc.total_ttc - doc.amount_paid
            if doc.amount_due >= doc.total_ttc:
                doc.status = "sent"  # revert to sent/validated state

    db.delete(payment)
    db.commit()
    return {"status": 200, "data": {"message": f"Payment {payment.reference} deleted and allocations reversed"}}


# ─────────────────────────────────────────────
# ALLOCATIONS (sub-resource)
# ─────────────────────────────────────────────

@router.get("/{payment_id}/allocations", response_model=StandardResponse[List[PaymentAllocationOut]])
async def list_payment_allocations(
    payment_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all allocations for a payment."""
    payment = db.query(Payment).filter(
        Payment.id == payment_id,
        Payment.enterprise_id == ctx.enterprise.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {"status": 200, "data": payment.allocations}
