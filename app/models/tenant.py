import uuid
from sqlalchemy import Column, String, Boolean, Numeric, Text, DateTime, ForeignKey, Integer, SmallInteger, CHAR
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.core.database import Base

class Enterprise(Base):
    __tablename__ = "enterprises"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(100), unique=True, nullable=False)

    # Dénomination
    legal_name = Column(String(300), nullable=False)
    trade_name = Column(String(300))
    legal_form = Column(String(50))  # legal_form_type enum
    sector = Column(String(150))
    activity_description = Column(Text)

    # Identifiants fiscaux & légaux (Maroc)
    ice = Column(String(15), unique=True)
    rc = Column(String(30))
    if_number = Column(String(20))
    taxe_professionnelle = Column(String(20))
    cnss = Column(String(20))
    capital_social = Column(Numeric(15, 2))
    capital_currency = Column(CHAR(3), server_default="MAD")

    # TVA
    tva_regime = Column(String(50), server_default="Encaissement")  # tva_regime_type enum
    tva_assujetti = Column(Boolean, server_default="true")

    # Coordonnées
    phone_main = Column(String(20))
    phone_secondary = Column(String(20))
    fax = Column(String(20))
    email_general = Column(String(255))
    email_facturation = Column(String(255))
    website = Column(String(300))

    # Adresse siège social
    address_street = Column(String(300))
    address_complement = Column(String(200))
    address_city = Column(String(100))
    address_zip = Column(String(10))
    address_region = Column(String(100))
    address_country = Column(CHAR(2), server_default="MA")

    # Adresse de facturation (si différente)
    billing_address_street = Column(String(300))
    billing_address_city = Column(String(100))
    billing_address_zip = Column(String(10))
    billing_address_country = Column(CHAR(2))

    # Coordonnées bancaires
    bank_name = Column(String(100))
    bank_rib = Column(String(24))
    bank_iban = Column(String(34))
    bank_swift = Column(String(11))
    bank_branch = Column(String(100))

    # Branding & assets
    logo_url = Column(String(500))
    logo_key = Column(String(300))
    stamp_url = Column(String(500))
    stamp_key = Column(String(300))
    signature_url = Column(String(500))
    signature_key = Column(String(300))
    primary_color = Column(CHAR(7), server_default="#1a1a1a")
    secondary_color = Column(CHAR(7), server_default="#4f4f4f")
    font_family = Column(String(50), server_default="Inter")

    # Préfixes de numérotation
    invoice_prefix = Column(String(10), server_default="FAC")
    quote_prefix = Column(String(10), server_default="DEV")
    po_prefix = Column(String(10), server_default="BDC")
    dn_prefix = Column(String(10), server_default="BDL")
    cn_prefix = Column(String(10), server_default="AVO")

    # Préférences documents
    default_language = Column(String(5), server_default="fr")
    default_currency = Column(CHAR(3), server_default="MAD")
    payment_terms_days = Column(SmallInteger, server_default="30")
    payment_conditions = Column(Text)
    invoice_footer = Column(Text)
    quote_validity_days = Column(SmallInteger, server_default="30")

    # Abonnement & statut
    plan = Column(String(50), server_default="free")  # plan_type enum
    is_active = Column(Boolean, nullable=False, server_default="true")
    is_verified = Column(Boolean, server_default="false")
    trial_ends_at = Column(DateTime(timezone=True))

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
