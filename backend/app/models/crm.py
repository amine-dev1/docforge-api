import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, ForeignKey, SmallInteger, CHAR, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Client(Base):
    __tablename__ = "clients"
    __table_args__ = (UniqueConstraint("enterprise_id", "code", name="uq_client_code"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(30))

    # Identification
    legal_name = Column(String(300), nullable=False)
    trade_name = Column(String(300))
    legal_form = Column(String(50))

    # Identifiants fiscaux
    ice = Column(String(15))
    rc = Column(String(30))
    if_number = Column(String(20))
    taxe_professionnelle = Column(String(20))
    cnss = Column(String(20))
    tva_number = Column(String(30))

    # Coordonnées
    phone = Column(String(20))
    mobile = Column(String(20))
    fax = Column(String(20))
    email = Column(String(255))
    website = Column(String(300))

    # Adresse principale
    address_street = Column(String(300))
    address_complement = Column(String(200))
    address_city = Column(String(100))
    address_zip = Column(String(10))
    address_region = Column(String(100))
    address_country = Column(CHAR(2), server_default="MA")

    # Adresse de livraison
    delivery_address_street = Column(String(300))
    delivery_address_city = Column(String(100))
    delivery_address_zip = Column(String(10))
    delivery_address_country = Column(CHAR(2))

    # Informations financières
    bank_name = Column(String(100))
    bank_rib = Column(String(24))
    bank_iban = Column(String(34))
    currency = Column(CHAR(3), server_default="MAD")
    payment_terms_days = Column(SmallInteger, server_default="30")
    credit_limit = Column(Numeric(15, 2))

    # CRM
    category = Column(String(100))
    source = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, server_default="true", nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    contacts = relationship("ClientContact", back_populates="client", cascade="all, delete-orphan")

class ClientContact(Base):
    __tablename__ = "client_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), ForeignKey("clients.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))
    department = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    mobile = Column(String(20))
    is_primary = Column(Boolean, server_default="false")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    client = relationship("Client", back_populates="contacts")

class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("enterprise_id", "code", name="uq_supplier_code"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(30))

    legal_name = Column(String(300), nullable=False)
    trade_name = Column(String(300))
    legal_form = Column(String(50))

    ice = Column(String(15))
    rc = Column(String(30))
    if_number = Column(String(20))
    taxe_professionnelle = Column(String(20))
    cnss = Column(String(20))

    phone = Column(String(20))
    mobile = Column(String(20))
    fax = Column(String(20))
    email = Column(String(255))
    website = Column(String(300))

    address_street = Column(String(300))
    address_complement = Column(String(200))
    address_city = Column(String(100))
    address_zip = Column(String(10))
    address_region = Column(String(100))
    address_country = Column(CHAR(2), server_default="MA")

    bank_name = Column(String(100))
    bank_rib = Column(String(24))
    bank_iban = Column(String(34))
    bank_swift = Column(String(11))
    currency = Column(CHAR(3), server_default="MAD")
    payment_terms_days = Column(SmallInteger, server_default="30")

    category = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, server_default="true", nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    contacts = relationship("SupplierContact", back_populates="supplier", cascade="all, delete-orphan")

class SupplierContact(Base):
    __tablename__ = "supplier_contacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_id = Column(UUID(as_uuid=True), ForeignKey("suppliers.id", ondelete="CASCADE"), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    title = Column(String(100))
    department = Column(String(100))
    email = Column(String(255))
    phone = Column(String(20))
    mobile = Column(String(20))
    is_primary = Column(Boolean, server_default="false")
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    supplier = relationship("Supplier", back_populates="contacts")
