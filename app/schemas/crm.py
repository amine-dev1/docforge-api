from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID


# ─────────────────────────────────────────────
# CLIENT CONTACT
# ─────────────────────────────────────────────

class ClientContactBase(BaseModel):
    first_name: str = Field(..., example="Ahmed")
    last_name: str = Field(..., example="Benali")
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None

class ClientContactCreate(ClientContactBase):
    pass

class ClientContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None

class ClientContactOut(ClientContactBase):
    id: UUID
    client_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# CLIENT
# ─────────────────────────────────────────────

class ClientBase(BaseModel):
    code: Optional[str] = Field(None, example="CLT-001")
    legal_name: str = Field(..., example="Société Exemple SARL")
    trade_name: Optional[str] = None
    legal_form: Optional[str] = None
    ice: Optional[str] = None
    rc: Optional[str] = None
    if_number: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    cnss: Optional[str] = None
    tva_number: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_complement: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_region: Optional[str] = None
    address_country: str = "MA"
    delivery_address_street: Optional[str] = None
    delivery_address_city: Optional[str] = None
    delivery_address_zip: Optional[str] = None
    delivery_address_country: Optional[str] = None
    bank_name: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_iban: Optional[str] = None
    currency: str = "MAD"
    payment_terms_days: int = 30
    credit_limit: Optional[Decimal] = None
    category: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class ClientCreate(ClientBase):
    contacts: Optional[List[ClientContactCreate]] = []

class ClientUpdate(BaseModel):
    code: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    legal_form: Optional[str] = None
    ice: Optional[str] = None
    rc: Optional[str] = None
    if_number: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    cnss: Optional[str] = None
    tva_number: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_complement: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_region: Optional[str] = None
    address_country: Optional[str] = None
    delivery_address_street: Optional[str] = None
    delivery_address_city: Optional[str] = None
    delivery_address_zip: Optional[str] = None
    delivery_address_country: Optional[str] = None
    bank_name: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_iban: Optional[str] = None
    currency: Optional[str] = None
    payment_terms_days: Optional[int] = None
    credit_limit: Optional[Decimal] = None
    category: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class ClientOut(ClientBase):
    id: UUID
    enterprise_id: UUID
    contacts: List[ClientContactOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# SUPPLIER CONTACT
# ─────────────────────────────────────────────

class SupplierContactBase(BaseModel):
    first_name: str = Field(..., example="Youssef")
    last_name: str = Field(..., example="Alaoui")
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: bool = False
    notes: Optional[str] = None

class SupplierContactCreate(SupplierContactBase):
    pass

class SupplierContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    department: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    is_primary: Optional[bool] = None
    notes: Optional[str] = None

class SupplierContactOut(SupplierContactBase):
    id: UUID
    supplier_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# SUPPLIER
# ─────────────────────────────────────────────

class SupplierBase(BaseModel):
    code: Optional[str] = Field(None, example="SUP-001")
    legal_name: str = Field(..., example="Fournisseur XYZ SARL")
    trade_name: Optional[str] = None
    legal_form: Optional[str] = None
    ice: Optional[str] = None
    rc: Optional[str] = None
    if_number: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    cnss: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_complement: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_region: Optional[str] = None
    address_country: str = "MA"
    bank_name: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_iban: Optional[str] = None
    bank_swift: Optional[str] = None
    currency: str = "MAD"
    payment_terms_days: int = 30
    category: Optional[str] = None
    notes: Optional[str] = None
    is_active: bool = True

class SupplierCreate(SupplierBase):
    contacts: Optional[List[SupplierContactCreate]] = []

class SupplierUpdate(BaseModel):
    code: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    legal_form: Optional[str] = None
    ice: Optional[str] = None
    rc: Optional[str] = None
    if_number: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    cnss: Optional[str] = None
    phone: Optional[str] = None
    mobile: Optional[str] = None
    fax: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_complement: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_region: Optional[str] = None
    address_country: Optional[str] = None
    bank_name: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_iban: Optional[str] = None
    bank_swift: Optional[str] = None
    currency: Optional[str] = None
    payment_terms_days: Optional[int] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class SupplierOut(SupplierBase):
    id: UUID
    enterprise_id: UUID
    contacts: List[SupplierContactOut] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
