# DocForge API - Project Status & Architecture

## 1. Project Overview
DocForge is an Enterprise Document Generation System backend built as a multi-tenant API. It handles automated document generation (invoices, quotes, etc.), multi-tenant isolation, user authentication, and secure access via API keys.

## 2. Project Architecture
The project is built using modern Python web technologies, following a modular, layered architecture pattern.

### Technologies Used
* **Framework:** FastAPI
* **Server:** Uvicorn
* **Database:** PostgreSQL with SQLAlchemy ORM and Alembic (migrations)
* **Data Validation:** Pydantic
* **Security:** PyJWT, Passlib (bcrypt), API Key Header Auth
* **PDF Generation:** ReportLab, WeasyPrint, Jinja2
* **Storage:** MinIO (S3-compatible)

### Directory Structure
```text
docforge-api/
├── app/
│   ├── api/            # API routers (v1 endpoints)
│   ├── core/           # Core configuration, database setup, exceptions, auth logic
│   ├── middleware/     # Custom middlewares (e.g., API key auth)
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic schemas for data validation
│   ├── services/       # Business logic layer (document generation, S3 ops)
│   ├── templates/      # Jinja2 templates for PDF generation
│   ├── main.py         # FastAPI application entry point
│   └── seed/           # Database seeding scripts
├── schema.sql          # Raw PostgreSQL database schema
├── requirements.txt    # Project dependencies
├── Dockerfile          # Docker image definition
└── docker-compose.yml  # Docker Compose configuration
```

### Architectural Patterns
* **Multi-Tenancy:** Each enterprise has its own isolated workspace. API endpoints enforce tenant isolation using the `X-API-Key` header mapped to `Enterprise` instances.
* **Role-Based Access Control (RBAC):** Users are assigned roles and permissions, restricting endpoint actions (Admin vs. Standard User).
* **Layered Design:** Routing (`api/`), Business Logic (`services/`), Data Access (`models/`), and Data Validation (`schemas/`) are strictly separated.

## 3. Database Architecture
The database is PostgreSQL, accessed via SQLAlchemy. The schema is highly normalized and structured around domains:

* **Core / Multi-Tenant:**
  * `Enterprise`: The central model representing a tenant workspace. All major entities are tied to an `enterprise_id`.
* **IAM / Authentication:**
  * `User`: System users linked to an enterprise.
  * `Role` & `Permission`: RBAC definitions.
  * `APIKey`: Tenant-specific API keys for authentication.
  * `RefreshToken` & `PasswordResetToken`: For authentication flows.
* **CRM:**
  * `Client` & `ClientContact`: Customers of the enterprise.
  * `Supplier` & `SupplierContact`: Vendors of the enterprise.
* **Catalogue:**
  * `Product`, `ProductCategory`, `UnitOfMeasure`, `TaxRate`: Inventory and billing configuration.
* **Documents:**
  * `Document`: Main entity for Invoices, Quotes, etc.
  * `DocumentLine`: Individual items on a document.
  * `DocumentSequence`: Auto-incrementing numbers for documents.
  * `DocumentAttachment`: Files associated with documents.
  * `EnterpriseDocConfig`: Branding and layout preferences for PDF generation.
* **Finance:**
  * `Payment` & `PaymentAllocation`: Tracking payments against documents.
* **System:**
  * `Subscription`, `AuditLog`, `Notification`, `WebhookEndpoint`, `WebhookLog`.

## 4. Requirements (Dependencies)
The core project dependencies defined in `requirements.txt`:
* `fastapi==0.136.1`
* `uvicorn[standard]==0.46.0`
* `sqlalchemy==2.0.49`
* `alembic==1.18.4`
* `pydantic==2.13.3`
* `pydantic-settings==2.14.0`
* `psycopg2-binary==2.9.12` (PostgreSQL driver)
* `reportlab==4.5.0`, `weasyprint==62.3`, `jinja2==3.1.4` (PDF Generation)
* `minio==7.2.5` (Object storage)
* `pyjwt==2.9.0`, `passlib[bcrypt]==1.7.4` (Security)
* `python-multipart`, `python-dotenv`, `email-validator`

## 5. Current Progress & Status

### ✅ Completed
1. **Initial Setup:** Project scaffolding, Docker configuration, and environment setup.
2. **Database Setup:** 
   * Complete PostgreSQL schema (`schema.sql`).
   * SQLAlchemy ORM models implemented across all domains.
   * Database initialization and seeding scripts implemented and executed.
3. **Core Infrastructure:**
   * FastAPI application initialized (`app/main.py`).
   * Swagger documentation integrated and enriched.
   * Database session management and core config implemented.
4. **Authentication & Security:**
   * Multi-tenant API key authentication middleware is implemented.
   * Security contexts are actively verifying the `X-API-Key` header.
5. **Basic API Endpoints:**
   * Tenant profile and configuration API endpoints.
   * Foundational CRUD structure.

### 🚧 Currently in Progress
* **Documents API (`app/api/v1/documents.py`):**
  * Routing and security contexts are established.
  * Read/List endpoints are partially implemented with basic multi-tenant filtering.
  * **Document Generation Logic:** The `create_invoice` endpoint is scaffolded but currently returns a mocked response (`"Document generation logic will be implemented here"`).
  * **Deletion:** Soft delete logic is mocked and needs full implementation.

### ⏳ Pending Next Steps
1. **Document Generation Engine:** Implement the business logic in `services/` to bind `Document` models with Jinja2 templates and generate PDFs using ReportLab/WeasyPrint.
2. **S3 Integration:** Hook up the MinIO client to upload and retrieve generated PDFs and document attachments.
3. **Finish Document Endpoints:** Connect the `/invoice` endpoint to the document generation engine. Implement complex relationships (Document Lines, Taxes, Payments).
4. **CRM & Catalogue APIs:** Build out endpoints to manage Clients, Products, and Taxes, as these are prerequisites for dynamic document generation.
5. **Alembic Migrations:** Setup Alembic history based on the current schema if not fully managed.
