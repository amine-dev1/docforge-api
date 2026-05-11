import hashlib
from typing import Optional
from dataclasses import dataclass
from fastapi import HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.exceptions import CustomAuthException
from app.models.api_key import APIKey
from app.models.tenant import Enterprise
from app.models.user import User, Role

# Registers X-API-Key as an official OpenAPI security scheme.
# FastAPI will surface the Authorize button + lock icon in Swagger UI.
api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Enter your tenant API key (issued by DocForge support or via the tenant API).",
    auto_error=False,
)

@dataclass
class SecurityContext:
    enterprise: Enterprise
    user: User
    is_admin: bool

async def get_current_enterprise(
    x_api_key: Optional[str] = Security(api_key_header),
    db: Session = Depends(get_db)
) -> SecurityContext:
    """
    Validate the X-API-KEY and return the security context (Enterprise + User + Role info).
    """
    if not x_api_key:
        raise CustomAuthException(
            message="Please authenticate with your user and password or the API KEY given by our support Team",
            error_type=401
        )
    
    # Hash the provided key to compare with stored hash
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    # Query the database for the active key
    db_key = db.query(APIKey).filter(
        APIKey.key_hash == key_hash,
        APIKey.is_active == True
    ).first()
    
    if not db_key:
        raise CustomAuthException(
            message="Invalid or inactive API Key",
            error_type=401
        )
    
    # Get associated enterprise
    enterprise = db.query(Enterprise).filter(Enterprise.id == db_key.enterprise_id).first()
    
    # Get creator user to check roles
    user = db.query(User).filter(User.id == db_key.created_by).first()
    
    if not enterprise or not user:
         raise CustomAuthException(
            message="Associated enterprise or user not found",
            error_type=404
        )

    # Check if user has "admin" role
    is_admin = (user.role.value == "admin") if hasattr(user.role, 'value') else (user.role == "admin")
        
    return SecurityContext(
        enterprise=enterprise,
        user=user,
        is_admin=is_admin
    )
