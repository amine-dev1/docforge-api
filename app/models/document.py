import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, ForeignKey, SmallInteger, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DocumentSequence(Base):
    __tablename__ = "document_sequences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String(30), nullable=False)
    year = Column(SmallInteger, nullable=False)
    last_seq = Column(Integer, server_default="0", nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))

    # Parties
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"))
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="SET NULL"))

    # Chaîne documentaire
    parent_doc_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="SET NULL"))

    # Identification
    type = Column(String(50), nullable=False)  # document_type enum
    number = Column(String(30), nullable=False)
    status = Column(String(50), server_default="draft", nullable=False)  # document_status enum
    language = Column(String(5), server_default="fr")
    currency = Column(String(3), server_default="MAD")
    exchange_rate = Column(Numeric(10, 6), server_default="1.000000")

    # Snapshots
    enterprise_snapshot = Column(JSONB, server_default="{}", nullable=False)
    counterpart_snapshot = Column(JSONB, server_default="{}", nullable=False)

    # Montants
    subtotal_ht = Column(Numeric(15, 2), server_default="0", nullable=False)
    total_discount = Column(Numeric(15, 2), server_default="0", nullable=False)
    total_tax = Column(Numeric(15, 2), server_default="0", nullable=False)
    total_ttc = Column(Numeric(15, 2), server_default="0", nullable=False)
    amount_paid = Column(Numeric(15, 2), server_default="0", nullable=False)
    amount_due = Column(Numeric(15, 2), server_default="0", nullable=False)

    # Textes
    notes = Column(Text)
    terms = Column(Text)
    footer = Column(Text)
    internal_notes = Column(Text)

    # PDF
    pdf_url = Column(String(500))
    pdf_key = Column(String(300))

    # Flags
    is_deleted = Column(Boolean, server_default="false", nullable=False)

    # Dates
    issued_at = Column(DateTime(timezone=True))
    due_at = Column(DateTime(timezone=True))
    validated_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    lines = relationship("DocumentLine", back_populates="document", cascade="all, delete-orphan")
    attachments = relationship("DocumentAttachment", back_populates="document", cascade="all, delete-orphan")

class DocumentLine(Base):
    __tablename__ = "document_lines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(UUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"))
    tax_rate_id = Column(UUID(as_uuid=True), ForeignKey("tax_rates.id", ondelete="SET NULL"))

    position = Column(SmallInteger, server_default="0", nullable=False)
    type = Column(String(50), server_default="product")  # document_line_type enum
    reference = Column(String(100))
    description = Column(Text, nullable=False)

    # Quantité & prix
    quantity = Column(Numeric(12, 3), server_default="1", nullable=False)
    unit = Column(String(20))
    unit_price_ht = Column(Numeric(12, 2), server_default="0", nullable=False)

    # Remise
    discount_pct = Column(Numeric(5, 2), server_default="0")
    discount_amount = Column(Numeric(12, 2), server_default="0")

    # Totaux
    line_total_ht = Column(Numeric(15, 2), server_default="0", nullable=False)
    tax_rate_value = Column(Numeric(5, 2), server_default="0")
    tax_amount = Column(Numeric(15, 2), server_default="0", nullable=False)
    line_total_ttc = Column(Numeric(15, 2), server_default="0", nullable=False)

    document = relationship("Document", back_populates="lines")

class DocumentAttachment(Base):
    __tablename__ = "document_attachments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(100))
    file_size_bytes = Column(Integer)
    file_url = Column(String(500))
    file_key = Column(String(300))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    document = relationship("Document", back_populates="attachments")

class EnterpriseDocConfig(Base):
    __tablename__ = "enterprise_doc_config"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    doc_type = Column(String(30), nullable=False)
    template_name = Column(String(50), server_default="classic")
    header_text = Column(Text)
    footer_text = Column(Text)
    show_logo = Column(Boolean, server_default="true")
    show_stamp = Column(Boolean, server_default="false")
    show_signature = Column(Boolean, server_default="false")
    show_bank_details = Column(Boolean, server_default="true")
    show_qr_code = Column(Boolean, server_default="false")
    custom_fields = Column(JSONB, server_default="[]")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
