import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, ForeignKey, SmallInteger, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from app.core.database import Base

class UnitOfMeasure(Base):
    __tablename__ = "units_of_measure"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    symbol = Column(String(10), nullable=False)
    is_default = Column(Boolean, server_default="false")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class TaxRate(Base):
    __tablename__ = "tax_rates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(100), nullable=False)
    label = Column(String(20), nullable=False)
    rate = Column(Numeric(5, 2), nullable=False)
    type = Column(String(30), server_default="TVA")
    is_default = Column(Boolean, server_default="false")
    is_active = Column(Boolean, server_default="true", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

class ProductCategory(Base):
    __tablename__ = "product_categories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL"))
    name = Column(String(150), nullable=False)
    code = Column(String(30))
    description = Column(Text)
    sort_order = Column(SmallInteger, server_default="0")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    children = relationship("ProductCategory", backref=backref("parent", remote_side=[id]))

class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    enterprise_id = Column(UUID(as_uuid=True), ForeignKey("enterprises.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL"))
    unit_id = Column(UUID(as_uuid=True), ForeignKey("units_of_measure.id", ondelete="SET NULL"))
    tax_rate_id = Column(UUID(as_uuid=True), ForeignKey("tax_rates.id", ondelete="SET NULL"))

    code = Column(String(50))
    reference = Column(String(100))
    name = Column(String(300), nullable=False)
    description = Column(Text)
    type = Column(String(50), server_default="product")  # product_type enum

    purchase_price_ht = Column(Numeric(12, 2), server_default="0")
    sale_price_ht = Column(Numeric(12, 2), server_default="0")

    is_active = Column(Boolean, server_default="true", nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
