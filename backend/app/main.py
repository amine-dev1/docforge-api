from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from fastapi.openapi.utils import get_openapi
from app.core.config import settings
from app.core.exceptions import CustomAuthException
from app.api.v1 import api_router

tags_metadata = [
    {
        "name": "Health",
        "description": "API health and database status checks.",
    },
    {
        "name": "Authentication",
        "description": "User registration, login, and token management.",
    },
    {
        "name": "Tenant",
        "description": "Tenant profile, branding, and API key management.",
    },
    {
        "name": "Documents",
        "description": "Generic endpoint for all document types.",
    },
    {
        "name": "Invoices",
        "description": "Create, update, and manage invoices.",
    },
    {
        "name": "Quotes",
        "description": "Create, update, and manage price quotes.",
    },
    {
        "name": "Clients",
        "description": "CRM — manage your customers and their contacts.",
    },
    {
        "name": "Suppliers",
        "description": "CRM — manage your suppliers and their contacts.",
    },
    {
        "name": "Catalogue",
        "description": "Products, categories, units of measure, and tax rates.",
    },
    {
        "name": "Payments",
        "description": "Record payments and allocate them to documents.",
    },
]

app = FastAPI(
    title="DocForge API",
    description="""
DocForge API - Enterprise Document Generation System.

## Authentication
Most endpoints require an **API Key** passed in the `X-API-Key` header.  
Click the **Authorize 🔓** button at the top-right of this page, enter your key, and all requests will include it automatically.

## Features
* **Automated Document Generation**: Create invoices, quotes, and more with 5 PDF templates.
* **Multi-tenant Architecture**: Isolated data and branding for each enterprise.
* **Secure Authentication**: API Key based authentication.
* **Cloud Storage**: Automatic PDF archiving to Google Drive.
    """,
    version="1.0.0",
    openapi_tags=tags_metadata,
    contact={
        "name": "DocForge Support",
        "url": "https://docforge.com/support",
        "email": "support@docforge.com",
    },
    license_info={
        "name": "Private",
    },
    debug=settings.DEBUG,
)


def custom_openapi():
    """Enrich the auto-generated OpenAPI schema with a nicer API key description."""
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
        tags=tags_metadata,
    )

    # FastAPI already adds ApiKeyAuth via the APIKeyHeader dependency.
    # We just enrich the description so it's clear in Swagger UI.
    schemes = schema.get("components", {}).get("securitySchemes", {})
    if "ApiKeyAuth" in schemes:
        schemes["ApiKeyAuth"]["description"] = (
            "Paste your tenant API key here. "
            "It will be sent as the `X-API-Key` header on every request."
        )

    app.openapi_schema = schema
    return app.openapi_schema


app.openapi = custom_openapi

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check at root with redirect to docs
@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": f"Welcome to DocForge API",
        "version": "1.0.0",
        "docs": "/docs",
    }

# Exception handlers
@app.exception_handler(CustomAuthException)
async def custom_auth_exception_handler(request: Request, exc: CustomAuthException):
    return JSONResponse(
        status_code=exc.error_type,
        content={
            "status": exc.error_type,
            "data": {
                "message": exc.message
            }
        },
    )

# Register routers
app.include_router(api_router, prefix="/api/v1")
