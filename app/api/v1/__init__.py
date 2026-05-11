from fastapi import APIRouter
from app.api.v1 import auth, tenant, documents, invoices, quotes, health, clients, suppliers, catalogue, payments

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(tenant.router)
api_router.include_router(documents.router)
api_router.include_router(invoices.router)
api_router.include_router(quotes.router)
api_router.include_router(clients.router)
api_router.include_router(suppliers.router)
api_router.include_router(catalogue.router)
api_router.include_router(payments.router)
