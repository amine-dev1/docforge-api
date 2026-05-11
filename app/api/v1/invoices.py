from typing import List
from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentOut, DocumentLineCreate, DocumentLineOut
from app.schemas.response import StandardResponse
from app.api.v1.documents import (
    list_documents, 
    create_document, 
    get_document, 
    update_document, 
    delete_document,
    list_document_lines,
    add_document_line,
    delete_document_line
)

router = APIRouter(prefix="/invoices", tags=["Invoices"])

@router.get("/", response_model=StandardResponse[List[DocumentOut]])
async def list_invoices(
    page: int = 1,
    size: int = 20,
    status_filter: str = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all invoices."""
    return await list_documents(page=page, size=size, doc_type="invoice", status_filter=status_filter, db=db, ctx=ctx)


@router.post("/", response_model=StandardResponse[DocumentOut], status_code=status.HTTP_201_CREATED)
async def create_invoice(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Create a new invoice."""
    doc_in.type = "invoice"
    return await create_document(doc_in=doc_in, db=db, ctx=ctx)


@router.get("/{invoice_id}", response_model=StandardResponse[DocumentOut])
async def get_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Get an invoice by ID."""
    return await get_document(doc_id=invoice_id, db=db, ctx=ctx)


@router.patch("/{invoice_id}", response_model=StandardResponse[DocumentOut])
async def update_invoice(
    invoice_id: UUID,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Update an invoice."""
    return await update_document(doc_id=invoice_id, doc_in=doc_in, db=db, ctx=ctx)


@router.delete("/{invoice_id}", response_model=StandardResponse[dict])
async def delete_invoice(
    invoice_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Soft-delete an invoice."""
    return await delete_document(doc_id=invoice_id, db=db, ctx=ctx)
