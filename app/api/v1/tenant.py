from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from sqlalchemy import cast, Integer, func
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.models.tenant import Enterprise
from app.schemas.tenant import EnterpriseCreate, EnterpriseUpdate, EnterpriseOut
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/tenant", tags=["Tenant"])

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
