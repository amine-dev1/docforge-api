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
    delete_document
)

router = APIRouter(prefix="/quotes", tags=["Quotes"])

@router.get("/", response_model=StandardResponse[List[DocumentOut]])
async def list_quotes(
    page: int = 1,
    size: int = 20,
    status_filter: str = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all quotes."""
    return await list_documents(page=page, size=size, doc_type="quote", status_filter=status_filter, db=db, ctx=ctx)


@router.post("/", response_model=StandardResponse[DocumentOut], status_code=status.HTTP_201_CREATED)
async def create_quote(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Create a new quote."""
    doc_in.type = "quote"
    return await create_document(doc_in=doc_in, db=db, ctx=ctx)


@router.get("/{quote_id}", response_model=StandardResponse[DocumentOut])
async def get_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Get a quote by ID."""
    return await get_document(doc_id=quote_id, db=db, ctx=ctx)


@router.patch("/{quote_id}", response_model=StandardResponse[DocumentOut])
async def update_quote(
    quote_id: UUID,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Update a quote."""
    return await update_document(doc_id=quote_id, doc_in=doc_in, db=db, ctx=ctx)


@router.delete("/{quote_id}", response_model=StandardResponse[dict])
async def delete_quote(
    quote_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Soft-delete a quote."""
    return await delete_document(doc_id=quote_id, db=db, ctx=ctx)
