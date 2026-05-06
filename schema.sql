-- =============================================================================
--  DocForge — Schéma PostgreSQL Complet
--  Version : 1.0.0
--  Base    : PostgreSQL 16+
-- =============================================================================

-- Extensions requises
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "unaccent";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- =============================================================================
--  TYPES ENUM
-- =============================================================================

CREATE TYPE legal_form_type AS ENUM (
    'SARL', 'SA', 'SAS', 'SNC',
    'Auto-entrepreneur', 'Association', 'Autre'
);

CREATE TYPE tva_regime_type AS ENUM (
    'Encaissement', 'Débit', 'Exonéré', 'Non assujetti'
);

CREATE TYPE plan_type AS ENUM (
    'free', 'pro', 'enterprise'
);

CREATE TYPE subscription_status AS ENUM (
    'trialing', 'active', 'past_due', 'cancelled', 'expired'
);

CREATE TYPE user_status AS ENUM (
    'active', 'inactive', 'suspended'
);

CREATE TYPE document_type AS ENUM (
    'invoice', 'quote', 'purchase_order', 'delivery_note',
    'credit_note', 'proforma'
);

CREATE TYPE document_status AS ENUM (
    'draft', 'validated', 'sent', 'partially_paid',
    'paid', 'overdue', 'cancelled'
);

CREATE TYPE payment_method AS ENUM (
    'bank_transfer', 'cheque', 'cash',
    'card', 'mobile_payment', 'other'
);

CREATE TYPE payment_status AS ENUM (
    'pending', 'confirmed', 'rejected', 'cancelled'
);

CREATE TYPE product_type AS ENUM (
    'product', 'service', 'consumable', 'package'
);

CREATE TYPE document_line_type AS ENUM (
    'product', 'service', 'discount', 'section', 'comment'
);

CREATE TYPE webhook_event AS ENUM (
    'document.created', 'document.validated', 'document.sent',
    'document.paid', 'payment.created', 'payment.confirmed',
    'client.created', 'supplier.created'
);


-- =============================================================================
--  DOMAINE 1 — ENTREPRISES & AUTH
-- =============================================================================

-- -----------------------------------------------------------------------------
--  TABLE : enterprises
-- -----------------------------------------------------------------------------
CREATE TABLE enterprises (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug                    VARCHAR(100) UNIQUE NOT NULL,

    -- Dénomination
    legal_name              VARCHAR(300) NOT NULL,
    trade_name              VARCHAR(300),
    legal_form              legal_form_type,
    sector                  VARCHAR(150),
    activity_description    TEXT,

    -- Identifiants fiscaux & légaux (Maroc)
    ice                     VARCHAR(15) UNIQUE,           -- Identifiant Commun de l'Entreprise
    rc                      VARCHAR(30),                  -- Registre de Commerce
    if_number               VARCHAR(20),                  -- Identifiant Fiscal
    taxe_professionnelle    VARCHAR(20),                  -- Patente
    cnss                    VARCHAR(20),                  -- N° CNSS employeur
    capital_social          NUMERIC(15, 2),
    capital_currency        CHAR(3) DEFAULT 'MAD',

    -- TVA
    tva_regime              tva_regime_type DEFAULT 'Encaissement',
    tva_assujetti           BOOLEAN DEFAULT TRUE,

    -- Coordonnées
    phone_main              VARCHAR(20),
    phone_secondary         VARCHAR(20),
    fax                     VARCHAR(20),
    email_general           VARCHAR(255),
    email_facturation       VARCHAR(255),
    website                 VARCHAR(300),

    -- Adresse siège social
    address_street          VARCHAR(300),
    address_complement      VARCHAR(200),
    address_city            VARCHAR(100),
    address_zip             VARCHAR(10),
    address_region          VARCHAR(100),
    address_country         CHAR(2) DEFAULT 'MA',

    -- Adresse de facturation (si différente)
    billing_address_street  VARCHAR(300),
    billing_address_city    VARCHAR(100),
    billing_address_zip     VARCHAR(10),
    billing_address_country CHAR(2),

    -- Coordonnées bancaires
    bank_name               VARCHAR(100),
    bank_rib                VARCHAR(24),                  -- RIB marocain 24 chiffres
    bank_iban               VARCHAR(34),
    bank_swift              VARCHAR(11),
    bank_branch             VARCHAR(100),

    -- Branding & assets
    logo_url                VARCHAR(500),
    logo_key                VARCHAR(300),                 -- Clé MinIO interne
    stamp_url               VARCHAR(500),
    stamp_key               VARCHAR(300),
    signature_url           VARCHAR(500),
    signature_key           VARCHAR(300),
    primary_color           CHAR(7) DEFAULT '#1a1a1a',
    secondary_color         CHAR(7) DEFAULT '#4f4f4f',
    font_family             VARCHAR(50) DEFAULT 'Inter',

    -- Préfixes de numérotation
    invoice_prefix          VARCHAR(10) DEFAULT 'FAC',
    quote_prefix            VARCHAR(10) DEFAULT 'DEV',
    po_prefix               VARCHAR(10) DEFAULT 'BDC',
    dn_prefix               VARCHAR(10) DEFAULT 'BDL',
    cn_prefix               VARCHAR(10) DEFAULT 'AVO',

    -- Préférences documents
    default_language        VARCHAR(5) DEFAULT 'fr',
    default_currency        CHAR(3) DEFAULT 'MAD',
    payment_terms_days      SMALLINT DEFAULT 30,
    payment_conditions      TEXT,
    invoice_footer          TEXT,
    quote_validity_days     SMALLINT DEFAULT 30,

    -- Abonnement & statut
    plan                    plan_type DEFAULT 'free',
    is_active               BOOLEAN DEFAULT TRUE NOT NULL,
    is_verified             BOOLEAN DEFAULT FALSE,
    trial_ends_at           TIMESTAMPTZ,

    created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : users
-- -----------------------------------------------------------------------------
CREATE TABLE users (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id       UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    first_name          VARCHAR(100) NOT NULL,
    last_name           VARCHAR(100) NOT NULL,
    email               VARCHAR(255) NOT NULL,
    hashed_password     VARCHAR(255) NOT NULL,
    status              user_status DEFAULT 'active',
    avatar_url          VARCHAR(500),
    last_login_at       TIMESTAMPTZ,
    last_login_ip       VARCHAR(45),
    failed_login_count  SMALLINT DEFAULT 0,
    locked_until        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, email)
);

-- -----------------------------------------------------------------------------
--  TABLE : roles
-- -----------------------------------------------------------------------------
CREATE TABLE roles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT,
    is_system       BOOLEAN DEFAULT FALSE,   -- TRUE = rôle système non supprimable
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, name)
);

-- -----------------------------------------------------------------------------
--  TABLE : user_roles  (junction)
-- -----------------------------------------------------------------------------
CREATE TABLE user_roles (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at     TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    assigned_by     UUID REFERENCES users(id) ON DELETE SET NULL,

    UNIQUE (user_id, role_id)
);

-- -----------------------------------------------------------------------------
--  TABLE : permissions
-- -----------------------------------------------------------------------------
CREATE TABLE permissions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    resource    VARCHAR(50) NOT NULL,   -- 'document', 'client', 'payment'...
    action      VARCHAR(50) NOT NULL,   -- 'create', 'read', 'update', 'delete', 'validate'
    description TEXT,

    UNIQUE (resource, action)
);

-- -----------------------------------------------------------------------------
--  TABLE : role_permissions  (junction)
-- -----------------------------------------------------------------------------
CREATE TABLE role_permissions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    role_id         UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id   UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,

    UNIQUE (role_id, permission_id)
);

-- -----------------------------------------------------------------------------
--  TABLE : api_keys
-- -----------------------------------------------------------------------------
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    name            VARCHAR(100) NOT NULL,
    key_hash        CHAR(64) UNIQUE NOT NULL,  -- SHA-256 de la clé brute
    key_preview     VARCHAR(8) NOT NULL,       -- 8 derniers chars pour affichage UI
    scopes          TEXT[],                    -- ['document:read', 'document:create']
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : refresh_tokens
-- -----------------------------------------------------------------------------
CREATE TABLE refresh_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      CHAR(64) UNIQUE NOT NULL,
    ip_address      VARCHAR(45),
    device_info     VARCHAR(300),
    is_revoked      BOOLEAN DEFAULT FALSE NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : password_reset_tokens
-- -----------------------------------------------------------------------------
CREATE TABLE password_reset_tokens (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash      CHAR(64) UNIQUE NOT NULL,
    is_used         BOOLEAN DEFAULT FALSE NOT NULL,
    expires_at      TIMESTAMPTZ NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);


-- =============================================================================
--  DOMAINE 2 — CRM (CLIENTS & FOURNISSEURS)
-- =============================================================================

-- -----------------------------------------------------------------------------
--  TABLE : clients
-- -----------------------------------------------------------------------------
CREATE TABLE clients (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id           UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    code                    VARCHAR(30),                   -- Code interne ex: CLI-0001

    -- Identification
    legal_name              VARCHAR(300) NOT NULL,
    trade_name              VARCHAR(300),
    legal_form              legal_form_type,

    -- Identifiants fiscaux
    ice                     VARCHAR(15),
    rc                      VARCHAR(30),
    if_number               VARCHAR(20),
    taxe_professionnelle    VARCHAR(20),
    cnss                    VARCHAR(20),
    tva_number              VARCHAR(30),

    -- Coordonnées
    phone                   VARCHAR(20),
    mobile                  VARCHAR(20),
    fax                     VARCHAR(20),
    email                   VARCHAR(255),
    website                 VARCHAR(300),

    -- Adresse principale
    address_street          VARCHAR(300),
    address_complement      VARCHAR(200),
    address_city            VARCHAR(100),
    address_zip             VARCHAR(10),
    address_region          VARCHAR(100),
    address_country         CHAR(2) DEFAULT 'MA',

    -- Adresse de livraison
    delivery_address_street VARCHAR(300),
    delivery_address_city   VARCHAR(100),
    delivery_address_zip    VARCHAR(10),
    delivery_address_country CHAR(2),

    -- Informations financières
    bank_name               VARCHAR(100),
    bank_rib                VARCHAR(24),
    bank_iban               VARCHAR(34),
    currency                CHAR(3) DEFAULT 'MAD',
    payment_terms_days      SMALLINT DEFAULT 30,
    credit_limit            NUMERIC(15, 2),

    -- CRM
    category                VARCHAR(100),               -- 'VIP', 'Standard', 'Nouveau'
    source                  VARCHAR(100),               -- 'Prospection', 'Référence'...
    notes                   TEXT,
    is_active               BOOLEAN DEFAULT TRUE NOT NULL,
    created_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, code)
);

-- -----------------------------------------------------------------------------
--  TABLE : client_contacts
-- -----------------------------------------------------------------------------
CREATE TABLE client_contacts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id       UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    title           VARCHAR(100),                -- 'Directeur Général', 'DAF'
    department      VARCHAR(100),
    email           VARCHAR(255),
    phone           VARCHAR(20),
    mobile          VARCHAR(20),
    is_primary      BOOLEAN DEFAULT FALSE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : suppliers
-- -----------------------------------------------------------------------------
CREATE TABLE suppliers (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id           UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    code                    VARCHAR(30),

    legal_name              VARCHAR(300) NOT NULL,
    trade_name              VARCHAR(300),
    legal_form              legal_form_type,

    ice                     VARCHAR(15),
    rc                      VARCHAR(30),
    if_number               VARCHAR(20),
    taxe_professionnelle    VARCHAR(20),
    cnss                    VARCHAR(20),

    phone                   VARCHAR(20),
    mobile                  VARCHAR(20),
    fax                     VARCHAR(20),
    email                   VARCHAR(255),
    website                 VARCHAR(300),

    address_street          VARCHAR(300),
    address_complement      VARCHAR(200),
    address_city            VARCHAR(100),
    address_zip             VARCHAR(10),
    address_region          VARCHAR(100),
    address_country         CHAR(2) DEFAULT 'MA',

    bank_name               VARCHAR(100),
    bank_rib                VARCHAR(24),
    bank_iban               VARCHAR(34),
    bank_swift              VARCHAR(11),
    currency                CHAR(3) DEFAULT 'MAD',
    payment_terms_days      SMALLINT DEFAULT 30,

    category                VARCHAR(100),
    notes                   TEXT,
    is_active               BOOLEAN DEFAULT TRUE NOT NULL,
    created_by              UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, code)
);

-- -----------------------------------------------------------------------------
--  TABLE : supplier_contacts
-- -----------------------------------------------------------------------------
CREATE TABLE supplier_contacts (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    supplier_id     UUID NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    title           VARCHAR(100),
    department      VARCHAR(100),
    email           VARCHAR(255),
    phone           VARCHAR(20),
    mobile          VARCHAR(20),
    is_primary      BOOLEAN DEFAULT FALSE,
    notes           TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);


-- =============================================================================
--  DOMAINE 3 — CATALOGUE
-- =============================================================================

-- -----------------------------------------------------------------------------
--  TABLE : units_of_measure
-- -----------------------------------------------------------------------------
CREATE TABLE units_of_measure (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    name            VARCHAR(50) NOT NULL,   -- 'Pièce', 'Kilogramme', 'Heure'
    symbol          VARCHAR(10) NOT NULL,   -- 'Pce', 'Kg', 'H'
    is_default      BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, symbol)
);

-- -----------------------------------------------------------------------------
--  TABLE : tax_rates
-- -----------------------------------------------------------------------------
CREATE TABLE tax_rates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,   -- 'TVA 20%'
    label           VARCHAR(20) NOT NULL,    -- '20%'
    rate            NUMERIC(5, 2) NOT NULL,  -- 20.00
    type            VARCHAR(30) DEFAULT 'TVA',
    is_default      BOOLEAN DEFAULT FALSE,
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, rate, type)
);

-- -----------------------------------------------------------------------------
--  TABLE : product_categories
-- -----------------------------------------------------------------------------
CREATE TABLE product_categories (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    parent_id       UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    name            VARCHAR(150) NOT NULL,
    code            VARCHAR(30),
    description     TEXT,
    sort_order      SMALLINT DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, code)
);

-- -----------------------------------------------------------------------------
--  TABLE : products
-- -----------------------------------------------------------------------------
CREATE TABLE products (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id       UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    category_id         UUID REFERENCES product_categories(id) ON DELETE SET NULL,
    unit_id             UUID REFERENCES units_of_measure(id) ON DELETE SET NULL,
    tax_rate_id         UUID REFERENCES tax_rates(id) ON DELETE SET NULL,

    code                VARCHAR(50),
    reference           VARCHAR(100),
    name                VARCHAR(300) NOT NULL,
    description         TEXT,
    type                product_type DEFAULT 'product',

    purchase_price_ht   NUMERIC(12, 2) DEFAULT 0,
    sale_price_ht       NUMERIC(12, 2) DEFAULT 0,

    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    created_by          UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, code)
);


-- =============================================================================
--  DOMAINE 4 — DOCUMENTS
-- =============================================================================

-- -----------------------------------------------------------------------------
--  TABLE : document_sequences
--  Compteur par (enterprise, type, année) — incrémenté via SELECT FOR UPDATE
-- -----------------------------------------------------------------------------
CREATE TABLE document_sequences (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    doc_type        VARCHAR(30) NOT NULL,    -- 'invoice', 'quote', etc.
    year            SMALLINT NOT NULL,
    last_seq        INTEGER DEFAULT 0 NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, doc_type, year)
);

-- -----------------------------------------------------------------------------
--  TABLE : documents
-- -----------------------------------------------------------------------------
CREATE TABLE documents (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id           UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    created_by              UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Parties
    client_id               UUID REFERENCES clients(id) ON DELETE SET NULL,
    supplier_id             UUID REFERENCES suppliers(id) ON DELETE SET NULL,

    -- Chaîne documentaire (Devis → BDC → BDL → Facture → Avoir)
    parent_doc_id           UUID REFERENCES documents(id) ON DELETE SET NULL,

    -- Identification
    type                    document_type NOT NULL,
    number                  VARCHAR(30) NOT NULL,         -- FAC-2026-00042
    status                  document_status DEFAULT 'draft' NOT NULL,
    language                VARCHAR(5) DEFAULT 'fr',
    currency                CHAR(3) DEFAULT 'MAD',
    exchange_rate           NUMERIC(10, 6) DEFAULT 1.000000,

    -- Snapshots figés au moment de création (immutables)
    enterprise_snapshot     JSONB NOT NULL DEFAULT '{}',  -- Données entreprise figées
    counterpart_snapshot    JSONB NOT NULL DEFAULT '{}',  -- Données client/fournisseur figées

    -- Montants calculés
    subtotal_ht             NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    total_discount          NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    total_tax               NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    total_ttc               NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    amount_paid             NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    amount_due              NUMERIC(15, 2) DEFAULT 0 NOT NULL,

    -- Textes libres
    notes                   TEXT,
    terms                   TEXT,
    footer                  TEXT,
    internal_notes          TEXT,   -- Notes internes non visibles sur le document

    -- PDF généré
    pdf_url                 VARCHAR(500),
    pdf_key                 VARCHAR(300),

    -- Flags
    is_deleted              BOOLEAN DEFAULT FALSE NOT NULL,

    -- Dates
    issued_at               TIMESTAMPTZ,
    due_at                  TIMESTAMPTZ,
    validated_at            TIMESTAMPTZ,
    sent_at                 TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, number)
);

-- -----------------------------------------------------------------------------
--  TABLE : document_lines
-- -----------------------------------------------------------------------------
CREATE TABLE document_lines (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id         UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    product_id          UUID REFERENCES products(id) ON DELETE SET NULL,
    tax_rate_id         UUID REFERENCES tax_rates(id) ON DELETE SET NULL,

    position            SMALLINT NOT NULL DEFAULT 0,    -- Ordre d'affichage
    type                document_line_type DEFAULT 'product',
    reference           VARCHAR(100),
    description         TEXT NOT NULL,

    -- Quantité & prix
    quantity            NUMERIC(12, 3) DEFAULT 1 NOT NULL,
    unit                VARCHAR(20),
    unit_price_ht       NUMERIC(12, 2) DEFAULT 0 NOT NULL,

    -- Remise
    discount_pct        NUMERIC(5, 2) DEFAULT 0,        -- % de remise
    discount_amount     NUMERIC(12, 2) DEFAULT 0,       -- Montant remise calculé

    -- Totaux
    line_total_ht       NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    tax_rate_value      NUMERIC(5, 2) DEFAULT 0,        -- Snapshot du taux appliqué
    tax_amount          NUMERIC(15, 2) DEFAULT 0 NOT NULL,
    line_total_ttc      NUMERIC(15, 2) DEFAULT 0 NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : document_attachments
-- -----------------------------------------------------------------------------
CREATE TABLE document_attachments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id     UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    uploaded_by     UUID REFERENCES users(id) ON DELETE SET NULL,
    file_name       VARCHAR(255) NOT NULL,
    file_type       VARCHAR(100),               -- 'application/pdf', 'image/jpeg'
    file_size_bytes INTEGER,
    file_url        VARCHAR(500),
    file_key        VARCHAR(300),
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : enterprise_doc_config
--  Configuration d'affichage par type de document
-- -----------------------------------------------------------------------------
CREATE TABLE enterprise_doc_config (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id       UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    doc_type            VARCHAR(30) NOT NULL,
    template_name       VARCHAR(50) DEFAULT 'classic',   -- 'classic','modern','minimal'
    header_text         TEXT,
    footer_text         TEXT,
    show_logo           BOOLEAN DEFAULT TRUE,
    show_stamp          BOOLEAN DEFAULT FALSE,
    show_signature      BOOLEAN DEFAULT FALSE,
    show_bank_details   BOOLEAN DEFAULT TRUE,
    show_qr_code        BOOLEAN DEFAULT FALSE,
    custom_fields       JSONB DEFAULT '[]',
    updated_at          TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (enterprise_id, doc_type)
);


-- =============================================================================
--  DOMAINE 5 — FINANCE
-- =============================================================================

-- -----------------------------------------------------------------------------
--  TABLE : payments
-- -----------------------------------------------------------------------------
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    created_by      UUID REFERENCES users(id) ON DELETE SET NULL,
    client_id       UUID REFERENCES clients(id) ON DELETE SET NULL,

    reference       VARCHAR(50) UNIQUE NOT NULL,     -- PAY-2026-00015
    method          payment_method DEFAULT 'bank_transfer',
    amount          NUMERIC(15, 2) NOT NULL,
    currency        CHAR(3) DEFAULT 'MAD',
    exchange_rate   NUMERIC(10, 6) DEFAULT 1.000000,
    amount_allocated NUMERIC(15, 2) DEFAULT 0,
    amount_remaining NUMERIC(15, 2) DEFAULT 0,

    -- Détails selon mode de paiement
    bank_reference  VARCHAR(100),                    -- Référence virement
    cheque_number   VARCHAR(50),                     -- N° chèque
    cheque_bank     VARCHAR(100),

    notes           TEXT,
    status          payment_status DEFAULT 'pending',
    payment_date    DATE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : payment_allocations
--  Répartition d'un paiement sur plusieurs factures
-- -----------------------------------------------------------------------------
CREATE TABLE payment_allocations (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    payment_id          UUID NOT NULL REFERENCES payments(id) ON DELETE CASCADE,
    document_id         UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    amount_allocated    NUMERIC(15, 2) NOT NULL,
    allocated_at        TIMESTAMPTZ DEFAULT NOW() NOT NULL,

    UNIQUE (payment_id, document_id)
);


-- =============================================================================
--  DOMAINE 6 — SYSTÈME
-- =============================================================================

-- -----------------------------------------------------------------------------
--  TABLE : subscriptions
-- -----------------------------------------------------------------------------
CREATE TABLE subscriptions (
    id                      UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id           UUID UNIQUE NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    plan                    plan_type DEFAULT 'free',
    status                  subscription_status DEFAULT 'trialing',
    doc_limit_monthly       INTEGER DEFAULT 50,
    docs_used_this_month    INTEGER DEFAULT 0,
    current_period_start    TIMESTAMPTZ,
    current_period_end      TIMESTAMPTZ,
    cancelled_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : audit_logs
-- -----------------------------------------------------------------------------
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID REFERENCES enterprises(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(100) NOT NULL,       -- 'document.created', 'payment.confirmed'
    resource_type   VARCHAR(50),
    resource_id     UUID,
    old_values      JSONB,
    new_values      JSONB,
    ip_address      VARCHAR(45),
    user_agent      VARCHAR(300),
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : notifications
-- -----------------------------------------------------------------------------
CREATE TABLE notifications (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(100) NOT NULL,       -- 'invoice.overdue', 'payment.received'
    title           VARCHAR(200) NOT NULL,
    message         TEXT,
    data            JSONB DEFAULT '{}',
    is_read         BOOLEAN DEFAULT FALSE,
    read_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : webhook_endpoints
-- -----------------------------------------------------------------------------
CREATE TABLE webhook_endpoints (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    enterprise_id   UUID NOT NULL REFERENCES enterprises(id) ON DELETE CASCADE,
    url             VARCHAR(500) NOT NULL,
    secret_hash     VARCHAR(64) NOT NULL,        -- HMAC-SHA256 signature secret
    events          webhook_event[] NOT NULL,    -- Liste des événements à écouter
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

-- -----------------------------------------------------------------------------
--  TABLE : webhook_logs
-- -----------------------------------------------------------------------------
CREATE TABLE webhook_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    webhook_id      UUID NOT NULL REFERENCES webhook_endpoints(id) ON DELETE CASCADE,
    event_type      VARCHAR(100) NOT NULL,
    payload         JSONB NOT NULL,
    http_status     SMALLINT,
    response_body   TEXT,
    attempt_number  SMALLINT DEFAULT 1,
    duration_ms     INTEGER,
    sent_at         TIMESTAMPTZ DEFAULT NOW() NOT NULL
);


-- =============================================================================
--  INDEX
-- =============================================================================

-- Enterprises
CREATE INDEX idx_enterprises_slug         ON enterprises(slug);
CREATE INDEX idx_enterprises_ice          ON enterprises(ice) WHERE ice IS NOT NULL;
CREATE INDEX idx_enterprises_plan         ON enterprises(plan);
CREATE INDEX idx_enterprises_is_active    ON enterprises(is_active);

-- Users
CREATE INDEX idx_users_enterprise         ON users(enterprise_id);
CREATE INDEX idx_users_email              ON users(email);
CREATE INDEX idx_users_enterprise_email   ON users(enterprise_id, email);

-- Roles & permissions
CREATE INDEX idx_user_roles_user          ON user_roles(user_id);
CREATE INDEX idx_user_roles_role          ON user_roles(role_id);
CREATE INDEX idx_role_permissions_role    ON role_permissions(role_id);

-- API Keys & tokens
CREATE INDEX idx_api_keys_enterprise      ON api_keys(enterprise_id);
CREATE INDEX idx_api_keys_hash            ON api_keys(key_hash);
CREATE INDEX idx_refresh_tokens_user      ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_hash      ON refresh_tokens(token_hash);

-- Clients
CREATE INDEX idx_clients_enterprise       ON clients(enterprise_id);
CREATE INDEX idx_clients_code             ON clients(enterprise_id, code);
CREATE INDEX idx_clients_ice              ON clients(ice) WHERE ice IS NOT NULL;
CREATE INDEX idx_clients_active           ON clients(enterprise_id, is_active);
-- Recherche full-text sur nom client
CREATE INDEX idx_clients_name_trgm        ON clients USING gin(legal_name gin_trgm_ops);

-- Suppliers
CREATE INDEX idx_suppliers_enterprise     ON suppliers(enterprise_id);
CREATE INDEX idx_suppliers_code           ON suppliers(enterprise_id, code);
CREATE INDEX idx_suppliers_ice            ON suppliers(ice) WHERE ice IS NOT NULL;

-- Products
CREATE INDEX idx_products_enterprise      ON products(enterprise_id);
CREATE INDEX idx_products_category        ON products(category_id);
CREATE INDEX idx_products_code            ON products(enterprise_id, code);
CREATE INDEX idx_products_active          ON products(enterprise_id, is_active);
CREATE INDEX idx_products_name_trgm       ON products USING gin(name gin_trgm_ops);

-- Documents
CREATE INDEX idx_documents_enterprise     ON documents(enterprise_id);
CREATE INDEX idx_documents_type           ON documents(enterprise_id, type);
CREATE INDEX idx_documents_status         ON documents(enterprise_id, status);
CREATE INDEX idx_documents_number         ON documents(enterprise_id, number);
CREATE INDEX idx_documents_client         ON documents(client_id);
CREATE INDEX idx_documents_supplier       ON documents(supplier_id);
CREATE INDEX idx_documents_parent         ON documents(parent_doc_id);
CREATE INDEX idx_documents_issued_at      ON documents(enterprise_id, issued_at DESC);
CREATE INDEX idx_documents_due_at         ON documents(enterprise_id, due_at)
    WHERE status NOT IN ('paid', 'cancelled');
CREATE INDEX idx_documents_not_deleted    ON documents(enterprise_id, type, status)
    WHERE is_deleted = FALSE;
-- Recherche dans snapshots JSON
CREATE INDEX idx_documents_snapshot_gin   ON documents USING gin(counterpart_snapshot);

-- Document lines
CREATE INDEX idx_doc_lines_document       ON document_lines(document_id);
CREATE INDEX idx_doc_lines_product        ON document_lines(product_id);
CREATE INDEX idx_doc_lines_position       ON document_lines(document_id, position);

-- Sequences
CREATE INDEX idx_sequences_lookup         ON document_sequences(enterprise_id, doc_type, year);

-- Payments
CREATE INDEX idx_payments_enterprise      ON payments(enterprise_id);
CREATE INDEX idx_payments_client          ON payments(client_id);
CREATE INDEX idx_payments_status          ON payments(enterprise_id, status);
CREATE INDEX idx_payments_date            ON payments(enterprise_id, payment_date DESC);
CREATE INDEX idx_allocations_payment      ON payment_allocations(payment_id);
CREATE INDEX idx_allocations_document     ON payment_allocations(document_id);

-- Audit logs
CREATE INDEX idx_audit_enterprise         ON audit_logs(enterprise_id);
CREATE INDEX idx_audit_user               ON audit_logs(user_id);
CREATE INDEX idx_audit_resource           ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_created            ON audit_logs(enterprise_id, created_at DESC);

-- Notifications
CREATE INDEX idx_notif_user_unread        ON notifications(user_id, is_read)
    WHERE is_read = FALSE;

-- Webhook logs
CREATE INDEX idx_webhook_logs_endpoint    ON webhook_logs(webhook_id);
CREATE INDEX idx_webhook_logs_sent        ON webhook_logs(sent_at DESC);


-- =============================================================================
--  FONCTIONS & TRIGGERS
-- =============================================================================

-- Trigger : mise à jour automatique de updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_enterprises_updated_at    BEFORE UPDATE ON enterprises    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_users_updated_at          BEFORE UPDATE ON users          FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_clients_updated_at        BEFORE UPDATE ON clients        FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_suppliers_updated_at      BEFORE UPDATE ON suppliers      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_products_updated_at       BEFORE UPDATE ON products       FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_documents_updated_at      BEFORE UPDATE ON documents      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_payments_updated_at       BEFORE UPDATE ON payments       FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_subscriptions_updated_at  BEFORE UPDATE ON subscriptions  FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_webhook_ep_updated_at     BEFORE UPDATE ON webhook_endpoints FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Fonction : génération du numéro de document (FAC-2026-00042)
CREATE OR REPLACE FUNCTION generate_document_number(
    p_enterprise_id UUID,
    p_doc_type      VARCHAR
) RETURNS VARCHAR AS $$
DECLARE
    v_year      SMALLINT := EXTRACT(YEAR FROM NOW());
    v_seq       INTEGER;
    v_prefix    VARCHAR(10);
    v_number    VARCHAR(30);
BEGIN
    -- Incrémentation atomique (FOR UPDATE = pas de doublon en concurrence)
    INSERT INTO document_sequences (id, enterprise_id, doc_type, year, last_seq)
    VALUES (uuid_generate_v4(), p_enterprise_id, p_doc_type, v_year, 1)
    ON CONFLICT (enterprise_id, doc_type, year)
    DO UPDATE SET last_seq = document_sequences.last_seq + 1,
                  updated_at = NOW()
    RETURNING last_seq INTO v_seq;

    -- Récupération du préfixe configuré par l'entreprise
    SELECT CASE p_doc_type
        WHEN 'invoice'        THEN invoice_prefix
        WHEN 'quote'          THEN quote_prefix
        WHEN 'purchase_order' THEN po_prefix
        WHEN 'delivery_note'  THEN dn_prefix
        WHEN 'credit_note'    THEN cn_prefix
        ELSE UPPER(p_doc_type)
    END INTO v_prefix
    FROM enterprises WHERE id = p_enterprise_id;

    -- Format : FAC-2026-00042
    v_number := v_prefix || '-' || v_year || '-' || LPAD(v_seq::TEXT, 5, '0');
    RETURN v_number;
END;
$$ LANGUAGE plpgsql;

-- Trigger : mise à jour de amount_due sur les documents après paiement
CREATE OR REPLACE FUNCTION sync_document_amounts()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE documents
    SET amount_paid = (
            SELECT COALESCE(SUM(pa.amount_allocated), 0)
            FROM payment_allocations pa
            JOIN payments p ON p.id = pa.payment_id
            WHERE pa.document_id = NEW.document_id
            AND p.status = 'confirmed'
        ),
        amount_due = total_ttc - (
            SELECT COALESCE(SUM(pa.amount_allocated), 0)
            FROM payment_allocations pa
            JOIN payments p ON p.id = pa.payment_id
            WHERE pa.document_id = NEW.document_id
            AND p.status = 'confirmed'
        ),
        status = CASE
            WHEN total_ttc <= (
                SELECT COALESCE(SUM(pa.amount_allocated), 0)
                FROM payment_allocations pa
                JOIN payments p ON p.id = pa.payment_id
                WHERE pa.document_id = NEW.document_id
                AND p.status = 'confirmed'
            ) THEN 'paid'::document_status
            WHEN (
                SELECT COALESCE(SUM(pa.amount_allocated), 0)
                FROM payment_allocations pa
                JOIN payments p ON p.id = pa.payment_id
                WHERE pa.document_id = NEW.document_id
                AND p.status = 'confirmed'
            ) > 0 THEN 'partially_paid'::document_status
            ELSE status
        END
    WHERE id = NEW.document_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sync_doc_amounts
    AFTER INSERT OR UPDATE ON payment_allocations
    FOR EACH ROW EXECUTE FUNCTION sync_document_amounts();


-- =============================================================================
--  DONNÉES INITIALES
-- =============================================================================

-- Permissions système
INSERT INTO permissions (id, resource, action, description) VALUES
    (uuid_generate_v4(), 'enterprise',  'read',     'Voir les infos entreprise'),
    (uuid_generate_v4(), 'enterprise',  'update',   'Modifier les infos entreprise'),
    (uuid_generate_v4(), 'user',        'create',   'Créer un utilisateur'),
    (uuid_generate_v4(), 'user',        'read',     'Voir les utilisateurs'),
    (uuid_generate_v4(), 'user',        'update',   'Modifier un utilisateur'),
    (uuid_generate_v4(), 'user',        'delete',   'Supprimer un utilisateur'),
    (uuid_generate_v4(), 'client',      'create',   'Créer un client'),
    (uuid_generate_v4(), 'client',      'read',     'Voir les clients'),
    (uuid_generate_v4(), 'client',      'update',   'Modifier un client'),
    (uuid_generate_v4(), 'client',      'delete',   'Supprimer un client'),
    (uuid_generate_v4(), 'supplier',    'create',   'Créer un fournisseur'),
    (uuid_generate_v4(), 'supplier',    'read',     'Voir les fournisseurs'),
    (uuid_generate_v4(), 'supplier',    'update',   'Modifier un fournisseur'),
    (uuid_generate_v4(), 'supplier',    'delete',   'Supprimer un fournisseur'),
    (uuid_generate_v4(), 'product',     'create',   'Créer un produit'),
    (uuid_generate_v4(), 'product',     'read',     'Voir les produits'),
    (uuid_generate_v4(), 'product',     'update',   'Modifier un produit'),
    (uuid_generate_v4(), 'product',     'delete',   'Supprimer un produit'),
    (uuid_generate_v4(), 'document',    'create',   'Créer un document'),
    (uuid_generate_v4(), 'document',    'read',     'Voir les documents'),
    (uuid_generate_v4(), 'document',    'update',   'Modifier un document'),
    (uuid_generate_v4(), 'document',    'delete',   'Supprimer un document'),
    (uuid_generate_v4(), 'document',    'validate', 'Valider un document'),
    (uuid_generate_v4(), 'document',    'send',     'Envoyer un document'),
    (uuid_generate_v4(), 'payment',     'create',   'Enregistrer un paiement'),
    (uuid_generate_v4(), 'payment',     'read',     'Voir les paiements'),
    (uuid_generate_v4(), 'payment',     'update',   'Modifier un paiement'),
    (uuid_generate_v4(), 'payment',     'delete',   'Supprimer un paiement'),
    (uuid_generate_v4(), 'report',      'read',     'Voir les rapports'),
    (uuid_generate_v4(), 'api_key',     'manage',   'Gérer les clés API');
