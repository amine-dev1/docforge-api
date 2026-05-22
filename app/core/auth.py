import hashlib
from typing import Optional
from dataclasses import dataclass
from fastapi import HTTPException, Depends, Security
from fastapi.security import APIKeyHeader, OAuth2PasswordBearer
from sqlalchemy.orm import Session
import jwt

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import CustomAuthException
from app.models.api_key import APIKey
from app.models.tenant import Enterprise
from app.models.user import User, Role

# Registers X-API-Key as an official OpenAPI security scheme.
api_key_header = APIKeyHeader(
    name="X-API-Key",
    scheme_name="ApiKeyAuth",
    description="Enter your tenant API key (issued by DocForge support or via the tenant API).",
    auto_error=False,
)

# Registers OAuth2 Bearer token (JWT) for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,
    description="Enter your JWT access token (obtained via /api/v1/auth/login)."
)

@dataclass
class SecurityContext:
    enterprise: Enterprise
    user: User
    is_admin: bool

async def get_current_enterprise(
    x_api_key: Optional[str] = Security(api_key_header),
    token: Optional[str] = Security(oauth2_scheme),
    db: Session = Depends(get_db)
) -> SecurityContext:
    """
    Validate the X-API-KEY or JWT token and return the security context.
    """
    if not x_api_key and not token:
        raise CustomAuthException(
            message="Please authenticate with your user and password or the API KEY given by our support Team",
            error_type=401
        )

    enterprise = None
    user = None

    if token:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            user_id: str = payload.get("sub")
            if not user_id:
                raise CustomAuthException(message="Invalid token payload", error_type=401)
            
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise CustomAuthException(message="User not found", error_type=404)
                
            enterprise = db.query(Enterprise).filter(Enterprise.id == user.enterprise_id).first()
            if not enterprise:
                raise CustomAuthException(message="Enterprise not found", error_type=404)
        except jwt.ExpiredSignatureError:
            raise CustomAuthException(message="Token expired", error_type=401)
        except jwt.InvalidTokenError:
            raise CustomAuthException(message="Invalid token", error_type=401)
            
    elif x_api_key:
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        db_key = db.query(APIKey).filter(
            APIKey.key_hash == key_hash,
            APIKey.is_active == True
        ).first()
        
        if not db_key:
            raise CustomAuthException(message="Invalid or inactive API Key", error_type=401)
        
        enterprise = db.query(Enterprise).filter(Enterprise.id == db_key.enterprise_id).first()
        user = db.query(User).filter(User.id == db_key.created_by).first()
        
        if not enterprise or not user:
             raise CustomAuthException(message="Associated enterprise or user not found", error_type=404)

    # Check if user has "admin" role
    is_admin = (user.role.value == "admin") if hasattr(user.role, 'value') else (user.role == "admin")
        
    return SecurityContext(
        enterprise=enterprise,
        user=user,
        is_admin=is_admin
    )
