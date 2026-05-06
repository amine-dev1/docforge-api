import uuid
from sqlalchemy import Column, String, Numeric, Text, DateTime, ForeignKey, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="SET NULL"))

    reference = Column(String(50), unique=True, nullable=False)
    method = Column(String(50), server_default="bank_transfer")  # payment_method enum
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), server_default="MAD")
    exchange_rate = Column(Numeric(10, 6), server_default="1.000000")
    amount_allocated = Column(Numeric(15, 2), server_default="0")
    amount_remaining = Column(Numeric(15, 2), server_default="0")

    # Détails
    bank_reference = Column(String(100))
    cheque_number = Column(String(50))
    cheque_bank = Column(String(100))

    notes = Column(Text)
    status = Column(String(50), server_default="pending")  # payment_status enum
    payment_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    allocations = relationship("PaymentAllocation", back_populates="payment", cascade="all, delete-orphan")

class PaymentAllocation(Base):
    __tablename__ = "payment_allocations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    payment_id = Column(UUID(as_uuid=True), ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    amount_allocated = Column(Numeric(15, 2), nullable=False)
    allocated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    payment = relationship("Payment", back_populates="allocations")
    document = relationship("Document")
