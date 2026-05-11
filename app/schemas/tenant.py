from pydantic import BaseModel, EmailStr, Field, HttpUrl
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from uuid import UUID

class EnterpriseBase(BaseModel):
    slug: str = Field(..., description="Unique identifier for the enterprise URL", example="my-awesome-company")
    legal_name: str = Field(..., description="Full legal name of the enterprise", example="My Awesome Company SARL")
    trade_name: Optional[str] = Field(None, description="Commercial or trade name", example="Awesome Co")
    legal_form: Optional[str] = Field(None, description="Legal structure (SARL, SA, etc.)", example="SARL")
    sector: Optional[str] = Field(None, description="Activity sector", example="Technology")
    activity_description: Optional[str] = Field(None, description="Brief description of activities")

    # Identifiers (Morocco specific)
    ice: Optional[str] = Field(None, description="Identifiant Commun de l'Entreprise", example="001234567000089")
    rc: Optional[str] = Field(None, description="Registre de Commerce", example="12345")
    if_number: Optional[str] = Field(None, description="Identifiant Fiscal", example="98765432")
    taxe_professionnelle: Optional[str] = Field(None, description="Patente", example="11223344")
    cnss: Optional[str] = Field(None, description="CNSS number", example="5566778")
    capital_social: Optional[Decimal] = Field(None, description="Social capital amount", example=100000.00)
    capital_currency: str = Field("MAD", description="Currency of capital", example="MAD")

    # TVA
    tva_regime: str = Field("Encaissement", description="VAT regime", example="Encaissement")
    tva_assujetti: bool = Field(True, description="Whether the enterprise is subject to VAT")

    # Contact
    phone_main: Optional[str] = Field(None, description="Main phone number", example="+212522000000")
    phone_secondary: Optional[str] = Field(None, description="Secondary phone number")
    fax: Optional[str] = Field(None, description="Fax number")
    email_general: Optional[EmailStr] = Field(None, description="General contact email", example="contact@company.com")
    email_facturation: Optional[EmailStr] = Field(None, description="Billing specific email", example="billing@company.com")
    website: Optional[str] = Field(None, description="Website URL", example="https://www.company.com")

    # Main Address
    address_street: Optional[str] = Field(None, description="Street address")
    address_complement: Optional[str] = Field(None, description="Address complement")
    address_city: Optional[str] = Field(None, description="City", example="Casablanca")
    address_zip: Optional[str] = Field(None, description="ZIP code", example="20000")
    address_region: Optional[str] = Field(None, description="Region")
    address_country: str = Field("MA", description="Country code (ISO)", example="MA")

    # Billing Address
    billing_address_street: Optional[str] = Field(None, description="Billing street address")
    billing_address_city: Optional[str] = Field(None, description="Billing city")
    billing_address_zip: Optional[str] = Field(None, description="Billing ZIP code")
    billing_address_country: Optional[str] = Field(None, description="Billing country code")

    # Bank Info
    bank_name: Optional[str] = Field(None, description="Bank name", example="Attijariwafa Bank")
    bank_rib: Optional[str] = Field(None, description="RIB (24 digits)", example="123456789012345678901234")
    bank_iban: Optional[str] = Field(None, description="IBAN")
    bank_swift: Optional[str] = Field(None, description="SWIFT/BIC code")
    bank_branch: Optional[str] = Field(None, description="Bank branch name")

    # Branding
    logo_url: Optional[str] = Field(None, description="URL to the logo")
    primary_color: str = Field("#1a1a1a", description="Primary brand color (hex)", example="#1a1a1a")
    secondary_color: str = Field("#4f4f4f", description="Secondary brand color (hex)", example="#4f4f4f")
    font_family: str = Field("Inter", description="Preferred font family")

    # Document Prefixes
    invoice_prefix: str = Field("FAC", description="Prefix for invoices")
    quote_prefix: str = Field("DEV", description="Prefix for quotes")
    po_prefix: str = Field("BDC", description="Prefix for purchase orders")
    dn_prefix: str = Field("BDL", description="Prefix for delivery notes")
    cn_prefix: str = Field("AVO", description="Prefix for credit notes")

    # Document Preferences
    default_language: str = Field("fr", description="Default document language")
    default_currency: str = Field("MAD", description="Default document currency")
    payment_terms_days: int = Field(30, description="Default payment terms in days")
    payment_conditions: Optional[str] = Field(None, description="Default payment conditions text")
    invoice_footer: Optional[str] = Field(None, description="Default invoice footer text")
    quote_validity_days: int = Field(30, description="Default quote validity in days")

class EnterpriseCreate(EnterpriseBase):
    pass

class EnterpriseUpdate(BaseModel):
    # All fields optional for partial updates
    slug: Optional[str] = None
    legal_name: Optional[str] = None
    trade_name: Optional[str] = None
    legal_form: Optional[str] = None
    sector: Optional[str] = None
    activity_description: Optional[str] = None
    ice: Optional[str] = None
    rc: Optional[str] = None
    if_number: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    cnss: Optional[str] = None
    capital_social: Optional[Decimal] = None
    capital_currency: Optional[str] = None
    tva_regime: Optional[str] = None
    tva_assujetti: Optional[bool] = None
    phone_main: Optional[str] = None
    phone_secondary: Optional[str] = None
    fax: Optional[str] = None
    email_general: Optional[EmailStr] = None
    email_facturation: Optional[EmailStr] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_complement: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_region: Optional[str] = None
    address_country: Optional[str] = None
    billing_address_street: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_zip: Optional[str] = None
    billing_address_country: Optional[str] = None
    bank_name: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_iban: Optional[str] = None
    bank_swift: Optional[str] = None
    bank_branch: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    font_family: Optional[str] = None
    invoice_prefix: Optional[str] = None
    quote_prefix: Optional[str] = None
    po_prefix: Optional[str] = None
    dn_prefix: Optional[str] = None
    cn_prefix: Optional[str] = None
    default_language: Optional[str] = None
    default_currency: Optional[str] = None
    payment_terms_days: Optional[int] = None
    payment_conditions: Optional[str] = None
    invoice_footer: Optional[str] = None
    quote_validity_days: Optional[int] = None

class EnterpriseOut(BaseModel):
    tenant_id: str = Field(..., alias="tenant_id")
    slug: str
    legal_name: str
    trade_name: Optional[str] = None
    legal_form: Optional[str] = None
    sector: Optional[str] = None
    activity_description: Optional[str] = None
    ice: Optional[str] = None
    rc: Optional[str] = None
    if_number: Optional[str] = None
    taxe_professionnelle: Optional[str] = None
    cnss: Optional[str] = None
    capital_social: Optional[Decimal] = None
    capital_currency: str = "MAD"
    tva_regime: str = "Encaissement"
    tva_assujetti: bool = True
    phone_main: Optional[str] = None
    phone_secondary: Optional[str] = None
    fax: Optional[str] = None
    email_general: Optional[EmailStr] = None
    email_facturation: Optional[EmailStr] = None
    website: Optional[str] = None
    address_street: Optional[str] = None
    address_complement: Optional[str] = None
    address_city: Optional[str] = None
    address_zip: Optional[str] = None
    address_region: Optional[str] = None
    address_country: str = "MA"
    billing_address_street: Optional[str] = None
    billing_address_city: Optional[str] = None
    billing_address_zip: Optional[str] = None
    billing_address_country: Optional[str] = None
    bank_name: Optional[str] = None
    bank_rib: Optional[str] = None
    bank_iban: Optional[str] = None
    bank_swift: Optional[str] = None
    bank_branch: Optional[str] = None
    logo_url: Optional[str] = None
    primary_color: str = "#1a1a1a"
    secondary_color: str = "#4f4f4f"
    font_family: str = "Inter"
    invoice_prefix: str = "FAC"
    quote_prefix: str = "DEV"
    po_prefix: str = "BDC"
    dn_prefix: str = "BDL"
    cn_prefix: str = "AVO"
    default_language: str = "fr"
    default_currency: str = "MAD"
    payment_terms_days: int = 30
    payment_conditions: Optional[str] = None
    invoice_footer: Optional[str] = None
    quote_validity_days: int = 30
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True
