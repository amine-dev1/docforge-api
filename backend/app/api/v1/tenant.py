from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from sqlalchemy import cast, Integer, func
from uuid import UUID
from pydantic import BaseModel, Field, SecretStr, EmailStr
import stripe
from app.services.resend_service import validate_resend_key

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.models.tenant import Enterprise
from app.schemas.tenant import EnterpriseCreate, EnterpriseUpdate, EnterpriseOut
from app.schemas.response import StandardResponse
from app.services.stripe_service import stripe_call, require_stripe, currency_factor

router = APIRouter(prefix="/tenant", tags=["Tenant"])

class ResendConnect(BaseModel):
    api_key: SecretStr = Field(min_length=1, max_length=255)
    from_email: EmailStr = Field(max_length=255)


@router.post('/integrations/resend', response_model=StandardResponse[EnterpriseOut])
def connect_resend(body: ResendConnect, db: Session = Depends(get_db),
                   ctx: SecurityContext = Security(get_current_enterprise)):
    key = body.api_key.get_secret_value().strip()
    validate_resend_key(key)
    ctx.enterprise.resend_api_key = key
    ctx.enterprise.resend_from_email = str(body.from_email)
    db.commit()
    db.refresh(ctx.enterprise)
    return {'status': 200, 'data': ctx.enterprise}


@router.delete('/integrations/resend', response_model=StandardResponse[EnterpriseOut])
def disconnect_resend(db: Session = Depends(get_db),
                      ctx: SecurityContext = Security(get_current_enterprise)):
    ctx.enterprise.resend_api_key = None
    ctx.enterprise.resend_from_email = None
    db.commit()
    db.refresh(ctx.enterprise)
    return {'status': 200, 'data': ctx.enterprise}


class StripeConnect(BaseModel):
    webhook_secret: SecretStr | None = Field(default=None, max_length=255)
    secret_key: SecretStr = Field(min_length=1, max_length=255)
    publishable_key: str = Field(min_length=1, max_length=255, pattern=r'^pk_(test|live)_')


@router.post('/integrations/stripe', response_model=StandardResponse[EnterpriseOut])
def connect_stripe(body: StripeConnect, db: Session = Depends(get_db),
                   ctx: SecurityContext = Security(get_current_enterprise)):
    key = body.secret_key.get_secret_value().strip()
    webhook_secret = body.webhook_secret.get_secret_value().strip() if body.webhook_secret else None
    if webhook_secret and not webhook_secret.startswith('whsec_'):
        raise HTTPException(400, 'La clé de signature doit commencer par whsec_.')
    stripe_call(stripe.Balance.retrieve, api_key=key)
    ctx.enterprise.stripe_webhook_secret = webhook_secret or None
    ctx.enterprise.stripe_secret_key = key
    ctx.enterprise.stripe_publishable_key = body.publishable_key.strip()
    db.commit()
    db.refresh(ctx.enterprise)
    return {'status': 200, 'data': ctx.enterprise}


@router.delete('/integrations/stripe', response_model=StandardResponse[EnterpriseOut])
def disconnect_stripe(db: Session = Depends(get_db),
                      ctx: SecurityContext = Security(get_current_enterprise)):
    ctx.enterprise.stripe_webhook_secret = None
    ctx.enterprise.stripe_secret_key = None
    ctx.enterprise.stripe_publishable_key = None
    db.commit()
    db.refresh(ctx.enterprise)
    return {'status': 200, 'data': ctx.enterprise}


@router.get('/integrations/stripe/dashboard', response_model=StandardResponse[dict])
def stripe_dashboard(ctx: SecurityContext = Security(get_current_enterprise)):
    key = require_stripe(ctx.enterprise)
    balance = stripe_call(stripe.Balance.retrieve, api_key=key)
    payments = stripe_call(stripe.PaymentIntent.list, api_key=key, limit=10)
    return {'status': 200, 'data': {
        'available': [{'amount': item.amount / currency_factor(item.currency),
                       'currency': item.currency.upper()} for item in balance.available],
        'payments': [{'id': item.id, 'amount': item.amount / currency_factor(item.currency),
                      'currency': item.currency.upper(), 'status': item.status,
                      'date': item.created, 'description': item.description} for item in payments.data],
    }}

@router.get("/me", response_model=StandardResponse[EnterpriseOut])
async def get_my_tenant(
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    Get the details of the enterprise associated with the provided API Key.
    """
    return {"status": 200, "data": ctx.enterprise}

@router.post("/", response_model=StandardResponse[EnterpriseOut], status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_in: EnterpriseCreate, 
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    Create a new tenant (Enterprise). Only Admins can do this globally.
    """
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create new tenants")
    # Check if slug already exists
    db_tenant = db.query(Enterprise).filter(Enterprise.slug == tenant_in.slug).first()
    if db_tenant:
        raise HTTPException(
            status_code=400,
            detail="A tenant with this slug already exists."
        )
    
    # Check if ICE already exists
    if tenant_in.ice:
        db_ice = db.query(Enterprise).filter(Enterprise.ice == tenant_in.ice).first()
        if db_ice:
            raise HTTPException(
                status_code=400,
                detail="A tenant with this ICE already exists."
            )

    # Generate next short_id (T1, T2, etc.)
    # We find the maximum numeric part currently in the database
    max_id_query = db.query(func.max(cast(func.substring(Enterprise.short_id, 2), Integer))).scalar()
    next_num = (max_id_query or 0) + 1
    new_short_id = f"T{next_num}"
    
    new_tenant = Enterprise(
        **tenant_in.model_dump(),
        short_id=new_short_id
    )
    db.add(new_tenant)
    db.commit()
    db.refresh(new_tenant)
    return {"status": 201, "data": new_tenant}


@router.get("/", response_model=StandardResponse[List[EnterpriseOut]])
async def list_tenants(
    page: int = 1, 
    size: int = 10, 
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    List tenants with pagination. Admins see all, users see only theirs.
    Ordered by the numeric part of T-ID.
    """
    if page < 1:
        page = 1
    
    skip = (page - 1) * size
    
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can list tenants")
        
    query = db.query(Enterprise)
    # Order by numeric part of short_id (strip 'T' and cast to int)
    tenants = query.order_by(
        cast(func.substring(Enterprise.short_id, 2), Integer)
    ).offset(skip).limit(size).all()
    
    return {"status": 200, "data": tenants}

@router.get("/{tenant_id}", response_model=StandardResponse[EnterpriseOut])
async def get_tenant(
    tenant_id: str, 
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    Get details of a specific tenant by T-ID or UUID.
    """
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can view tenant details by ID")

    # Try searching by short_id (T1, T2...)
    tenant = db.query(Enterprise).filter(func.upper(Enterprise.short_id) == tenant_id.upper()).first()
    
    # Fallback to UUID if not found and input looks like a UUID
    if not tenant:
        try:
            tenant = db.query(Enterprise).filter(Enterprise.id == tenant_id).first()
        except Exception:
            db.rollback()

    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return {"status": 200, "data": tenant}

@router.put("/{tenant_id}", response_model=StandardResponse[EnterpriseOut])
async def update_tenant(
    tenant_id: str, 
    tenant_in: EnterpriseUpdate, 
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    Update a tenant's information.
    """
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can update tenants")

    db_tenant = db.query(Enterprise).filter(func.upper(Enterprise.short_id) == tenant_id.upper()).first()
    if not db_tenant:
        try:
            db_tenant = db.query(Enterprise).filter(Enterprise.id == tenant_id).first()
        except Exception:
            db.rollback()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    update_data = tenant_in.model_dump(exclude_unset=True)
    
    # If slug is being updated, check for collisions
    if "slug" in update_data and update_data["slug"] != db_tenant.slug:
        collision = db.query(Enterprise).filter(Enterprise.slug == update_data["slug"]).first()
        if collision:
            raise HTTPException(status_code=400, detail="Slug already in use")

    for field, value in update_data.items():
        setattr(db_tenant, field, value)
    
    db.commit()
    db.refresh(db_tenant)
    return {"status": 200, "data": db_tenant}

@router.delete("/{tenant_id}", response_model=StandardResponse[dict])
async def delete_tenant(
    tenant_id: str, 
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise)
):
    """
    Hard delete a tenant. Admins only.
    """
    if not ctx.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can delete tenants")

    db_tenant = db.query(Enterprise).filter(func.upper(Enterprise.short_id) == tenant_id.upper()).first()
    if not db_tenant:
        try:
            db_tenant = db.query(Enterprise).filter(Enterprise.id == tenant_id).first()
        except Exception:
            db.rollback()
    if not db_tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    tenant_name = db_tenant.legal_name
    db.delete(db_tenant)
    db.commit()
    
    return {
        "status": 200, 
        "data": {"message": f"Tenant {tenant_name} deleted successfully"}
    }

@router.get("/profile", response_model=EnterpriseOut, include_in_schema=False)
async def get_profile():
    # This is kept for compatibility but redirected or deprecated by /{id}
    # In a real app, this would use the current user's enterprise_id
    raise HTTPException(status_code=405, detail="Use /{id} endpoint or authenticated /me/enterprise")
