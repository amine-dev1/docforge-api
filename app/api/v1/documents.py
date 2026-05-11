from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status, UploadFile, File
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.services.drive_service import DriveService
from app.services.pdf_service import generate_pdf
from app.models.document import Document, DocumentLine, DocumentSequence
from app.models.crm import Client
from app.schemas.document import DocumentCreate, DocumentUpdate, DocumentOut, DocumentLineCreate, DocumentLineOut
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


# ─────────────────────────────────────────────
# HELPER: auto-generate document number
# ─────────────────────────────────────────────

def _generate_doc_number(db: Session, enterprise_id, doc_type: str, prefixes: dict) -> str:
    """Increment DocumentSequence and return the formatted document number."""
    year = datetime.utcnow().year
    prefix_map = {
        "invoice": prefixes.get("invoice_prefix", "FAC"),
        "quote": prefixes.get("quote_prefix", "DEV"),
        "purchase_order": prefixes.get("po_prefix", "BDC"),
        "delivery_note": prefixes.get("dn_prefix", "BDL"),
        "credit_note": prefixes.get("cn_prefix", "AVO"),
    }
    prefix = prefix_map.get(doc_type, doc_type.upper()[:3])

    seq = db.query(DocumentSequence).filter(
        DocumentSequence.enterprise_id == enterprise_id,
        DocumentSequence.doc_type == doc_type,
        DocumentSequence.year == year,
    ).first()

    if not seq:
        seq = DocumentSequence(enterprise_id=enterprise_id, doc_type=doc_type, year=year, last_seq=0)
        db.add(seq)
        db.flush()

    seq.last_seq += 1
    db.flush()
    return f"{prefix}-{year}-{seq.last_seq:05d}"


# ─────────────────────────────────────────────
# HELPER: compute line totals
# ─────────────────────────────────────────────

def _compute_line(line_data: dict) -> dict:
    """Calculate derived amounts for a document line."""
    from decimal import Decimal
    qty = Decimal(str(line_data.get("quantity", 1)))
    unit_price = Decimal(str(line_data.get("unit_price_ht", 0)))
    discount_pct = Decimal(str(line_data.get("discount_pct", 0)))
    discount_amount = Decimal(str(line_data.get("discount_amount", 0)))
    tax_rate_value = Decimal(str(line_data.get("tax_rate_value", 0)))

    base = qty * unit_price
    if discount_pct:
        discount_amount = base * discount_pct / 100
    line_ht = base - discount_amount
    tax_amount = line_ht * tax_rate_value / 100
    line_ttc = line_ht + tax_amount

    line_data["discount_amount"] = discount_amount
    line_data["line_total_ht"] = line_ht
    line_data["tax_amount"] = tax_amount
    line_data["line_total_ttc"] = line_ttc
    return line_data


# ─────────────────────────────────────────────
# LIST & CREATE DOCUMENTS
# ─────────────────────────────────────────────

@router.get("/", response_model=StandardResponse[List[DocumentOut]])
async def list_documents(
    page: int = 1,
    size: int = 20,
    doc_type: str = None,
    status_filter: str = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all documents for the authenticated tenant, with optional filters."""
    query = db.query(Document).filter(
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False
    )
    if doc_type:
        query = query.filter(Document.type == doc_type)
    if status_filter:
        query = query.filter(Document.status == status_filter)
    docs = query.order_by(Document.created_at.desc()).offset((page - 1) * size).limit(size).all()
    return {"status": 200, "data": docs}


@router.post("/", response_model=StandardResponse[DocumentOut], status_code=status.HTTP_201_CREATED)
async def create_document(
    doc_in: DocumentCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """
    Create any type of document (invoice, quote, credit_note, etc.).
    Lines are passed inline; totals are computed server-side.
    """
    from decimal import Decimal

    enterprise = ctx.enterprise
    prefixes = {
        "invoice_prefix": enterprise.invoice_prefix,
        "quote_prefix": enterprise.quote_prefix,
        "po_prefix": enterprise.po_prefix,
        "dn_prefix": enterprise.dn_prefix,
        "cn_prefix": enterprise.cn_prefix,
    }

    number = _generate_doc_number(db, enterprise.id, doc_in.type, prefixes)

    lines_data = doc_in.lines or []
    doc_data = doc_in.model_dump(exclude={"lines"})

    doc = Document(
        **doc_data,
        enterprise_id=enterprise.id,
        created_by=ctx.user.id,
        number=number,
        status="draft",
    )
    db.add(doc)
    db.flush()

    subtotal_ht = Decimal(0)
    total_discount = Decimal(0)
    total_tax = Decimal(0)

    for idx, line_schema in enumerate(lines_data):
        line_dict = line_schema.model_dump()
        line_dict["position"] = line_dict.get("position") or idx
        line_dict = _compute_line(line_dict)

        line = DocumentLine(**line_dict, document_id=doc.id)
        db.add(line)

        subtotal_ht += line_dict["line_total_ht"]
        total_discount += line_dict["discount_amount"]
        total_tax += line_dict["tax_amount"]

    doc.subtotal_ht = subtotal_ht
    doc.total_discount = total_discount
    doc.total_tax = total_tax
    doc.total_ttc = subtotal_ht + total_tax
    doc.amount_due = doc.total_ttc

    db.commit()
    db.refresh(doc)

    # ── AUTO-GENERATE PDF & UPLOAD TO GOOGLE DRIVE ──
    try:
        # Fetch the client for the PDF template
        client_obj = None
        if doc.client_id:
            client_obj = db.query(Client).filter(Client.id == doc.client_id).first()

        # Reload lines from DB (they now have IDs)
        doc_lines = db.query(DocumentLine).filter(DocumentLine.document_id == doc.id).order_by(DocumentLine.position).all()

        # Generate PDF in memory
        pdf_bytes = await run_in_threadpool(
            generate_pdf, doc, enterprise, client_obj, doc_lines
        )

        # Upload to Google Drive
        filename = f"{doc.number}.pdf"
        drive_result = await run_in_threadpool(
            _get_drive_client().upload_file, pdf_bytes, filename, "application/pdf"
        )

        # Store the Drive link back in the document
        doc.pdf_url = drive_result.get("webViewLink")
        doc.pdf_key = drive_result.get("id")
        db.commit()
        db.refresh(doc)
    except Exception as pdf_err:
        # PDF generation failure should NOT block the document creation
        import logging
        logging.getLogger(__name__).warning(f"PDF generation/upload failed for {doc.number}: {pdf_err}")

    return {"status": 201, "data": doc}


# ─────────────────────────────────────────────
# SINGLE DOCUMENT
# ─────────────────────────────────────────────

@router.get("/{doc_id}", response_model=StandardResponse[DocumentOut])
async def get_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Get full details of a document, including all lines."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": 200, "data": doc}


@router.patch("/{doc_id}", response_model=StandardResponse[DocumentOut])
async def update_document(
    doc_id: UUID,
    doc_in: DocumentUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """
    Update document metadata (status, dates, notes, etc.).
    Only allowed on draft documents unless you are changing status.
    """
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    for field, value in doc_in.model_dump(exclude_none=True).items():
        setattr(doc, field, value)

    db.commit()
    db.refresh(doc)
    return {"status": 200, "data": doc}


@router.delete("/{doc_id}", response_model=StandardResponse[dict])
async def delete_document(
    doc_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Soft-delete a document (sets is_deleted=True). Only draft documents can be deleted."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="Only draft documents can be deleted")

    doc.is_deleted = True
    db.commit()
    return {"status": 200, "data": {"message": f"Document {doc.number} deleted"}}


# ─────────────────────────────────────────────
# DOCUMENT LINES (sub-resource)
# ─────────────────────────────────────────────

@router.get("/{doc_id}/lines", response_model=StandardResponse[List[DocumentLineOut]])
async def list_document_lines(
    doc_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all lines of a document."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": 200, "data": doc.lines}


@router.post("/{doc_id}/lines", response_model=StandardResponse[DocumentLineOut], status_code=status.HTTP_201_CREATED)
async def add_document_line(
    doc_id: UUID,
    line_in: DocumentLineCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Add a line to a draft document and recompute totals."""
    from decimal import Decimal

    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="Cannot add lines to a non-draft document")

    line_dict = line_in.model_dump()
    if not line_dict.get("position"):
        line_dict["position"] = len(doc.lines)
    line_dict = _compute_line(line_dict)

    line = DocumentLine(**line_dict, document_id=doc_id)
    db.add(line)
    db.flush()

    # Recompute document totals
    doc.subtotal_ht = sum(l.line_total_ht for l in doc.lines)
    doc.total_discount = sum(l.discount_amount for l in doc.lines)
    doc.total_tax = sum(l.tax_amount for l in doc.lines)
    doc.total_ttc = doc.subtotal_ht + doc.total_tax
    doc.amount_due = doc.total_ttc - doc.amount_paid

    db.commit()
    db.refresh(line)
    return {"status": 201, "data": line}


@router.delete("/{doc_id}/lines/{line_id}", response_model=StandardResponse[dict])
async def delete_document_line(
    doc_id: UUID,
    line_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Remove a line from a draft document and recompute totals."""
    doc = db.query(Document).filter(
        Document.id == doc_id,
        Document.enterprise_id == ctx.enterprise.id,
        Document.is_deleted == False,
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc.status != "draft":
        raise HTTPException(status_code=400, detail="Cannot delete lines from a non-draft document")

    line = db.query(DocumentLine).filter(
        DocumentLine.id == line_id,
        DocumentLine.document_id == doc_id,
    ).first()
    if not line:
        raise HTTPException(status_code=404, detail="Line not found")

    db.delete(line)
    db.flush()

    # Recompute totals after deletion
    remaining = db.query(DocumentLine).filter(DocumentLine.document_id == doc_id).all()
    from decimal import Decimal
    doc.subtotal_ht = sum(l.line_total_ht for l in remaining) if remaining else Decimal(0)
    doc.total_discount = sum(l.discount_amount for l in remaining) if remaining else Decimal(0)
    doc.total_tax = sum(l.tax_amount for l in remaining) if remaining else Decimal(0)
    doc.total_ttc = doc.subtotal_ht + doc.total_tax
    doc.amount_due = doc.total_ttc - doc.amount_paid

    db.commit()
    return {"status": 200, "data": {"message": "Line removed and totals recomputed"}}


# ─────────────────────────────────────────────
# GOOGLE DRIVE UPLOAD
# ─────────────────────────────────────────────

drive_client = None  # Lazy-initialized on first upload to avoid blocking server startup


def _get_drive_client():
    from app.core.config import settings
    global drive_client
    if drive_client is None:
        drive_client = DriveService(
            settings.GOOGLE_DRIVE_CREDENTIALS,
            settings.GOOGLE_DRIVE_FOLDER_ID
        )
    return drive_client

@router.post("/upload/invoice")
async def upload_invoice(
    file: UploadFile = File(...),
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    Upload a generated PDF invoice directly to Google Drive asynchronously.
    """
    try:
        contents = await file.read()
        result = await run_in_threadpool(
            _get_drive_client().upload_file, 
            contents, 
            file.filename, 
            file.content_type
        )
        
        return {
            "status": "success",
            "file_id": result.get("id"),
            "filename": result.get("name"),
            "url": result.get("webViewLink")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
