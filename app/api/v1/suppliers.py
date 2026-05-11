from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.models.crm import Supplier, SupplierContact
from app.schemas.crm import (
    SupplierCreate, SupplierUpdate, SupplierOut,
    SupplierContactCreate, SupplierContactUpdate, SupplierContactOut,
)
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/suppliers", tags=["Suppliers"])


# ─────────────────────────────────────────────
# SUPPLIERS
# ─────────────────────────────────────────────

@router.get("/", response_model=StandardResponse[List[SupplierOut]])
async def list_suppliers(
    page: int = 1,
    size: int = 20,
    is_active: bool = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all suppliers for the authenticated tenant."""
    query = db.query(Supplier).filter(Supplier.enterprise_id == ctx.enterprise.id)
    if is_active is not None:
        query = query.filter(Supplier.is_active == is_active)
    suppliers = query.offset((page - 1) * size).limit(size).all()
    return {"status": 200, "data": suppliers}


@router.post("/", response_model=StandardResponse[SupplierOut], status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Create a new supplier."""
    contacts_data = supplier_in.contacts or []
    supplier_data = supplier_in.model_dump(exclude={"contacts"})

    supplier = Supplier(**supplier_data, enterprise_id=ctx.enterprise.id, created_by=ctx.user.id)
    db.add(supplier)
    db.flush()

    for c in contacts_data:
        contact = SupplierContact(**c.model_dump(), supplier_id=supplier.id)
        db.add(contact)

    db.commit()
    db.refresh(supplier)
    return {"status": 201, "data": supplier}


@router.get("/{supplier_id}", response_model=StandardResponse[SupplierOut])
async def get_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Get a single supplier by ID."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"status": 200, "data": supplier}


@router.patch("/{supplier_id}", response_model=StandardResponse[SupplierOut])
async def update_supplier(
    supplier_id: UUID,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Partially update a supplier."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    for field, value in supplier_in.model_dump(exclude_none=True).items():
        setattr(supplier, field, value)

    db.commit()
    db.refresh(supplier)
    return {"status": 200, "data": supplier}


@router.delete("/{supplier_id}", response_model=StandardResponse[dict])
async def delete_supplier(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Soft-delete a supplier (sets is_active=False)."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    supplier.is_active = False
    db.commit()
    return {"status": 200, "data": {"message": f"Supplier {supplier.legal_name} deactivated"}}


# ─────────────────────────────────────────────
# SUPPLIER CONTACTS (sub-resource)
# ─────────────────────────────────────────────

@router.get("/{supplier_id}/contacts", response_model=StandardResponse[List[SupplierContactOut]])
async def list_supplier_contacts(
    supplier_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all contacts for a supplier."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return {"status": 200, "data": supplier.contacts}


@router.post("/{supplier_id}/contacts", response_model=StandardResponse[SupplierContactOut], status_code=status.HTTP_201_CREATED)
async def add_supplier_contact(
    supplier_id: UUID,
    contact_in: SupplierContactCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Add a contact to a supplier."""
    supplier = db.query(Supplier).filter(
        Supplier.id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    contact = SupplierContact(**contact_in.model_dump(), supplier_id=supplier_id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"status": 201, "data": contact}


@router.patch("/{supplier_id}/contacts/{contact_id}", response_model=StandardResponse[SupplierContactOut])
async def update_supplier_contact(
    supplier_id: UUID,
    contact_id: UUID,
    contact_in: SupplierContactUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Update a supplier contact."""
    contact = db.query(SupplierContact).join(Supplier).filter(
        SupplierContact.id == contact_id,
        SupplierContact.supplier_id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in contact_in.model_dump(exclude_none=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return {"status": 200, "data": contact}


@router.delete("/{supplier_id}/contacts/{contact_id}", response_model=StandardResponse[dict])
async def delete_supplier_contact(
    supplier_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Delete a supplier contact permanently."""
    contact = db.query(SupplierContact).join(Supplier).filter(
        SupplierContact.id == contact_id,
        SupplierContact.supplier_id == supplier_id,
        Supplier.enterprise_id == ctx.enterprise.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"status": 200, "data": {"message": "Contact deleted"}}
