import time
import hashlib
from fastapi import Request, HTTPException, status
from sqlalchemy.orm import Session
from app.models.api_key import APIKey
from fastapi import Depends
from app.core.database import SessionLocal

def get_api_key(request: Request) -> str:
    """Extract API key from X-API-Key header"""
    api_key = request.headers.get("X-API-Key")
    if not api_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
    return api_key

def validate_api_key(api_key: str, db: Session = None):
    """Validate the provided API key against database records.
    Raises HTTPException if invalid, inactive or expired.
    """
    if db is None:
        db = SessionLocal()
    # Hash the raw key to compare with stored hash
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    record = db.query(ApiKey).filter(ApiKey.key_hash == key_hash, ApiKey.is_active == True).first()
    if not record:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
    # Optional: check expiration
    if record.expires_at and record.expires_at < time.time():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key expired")
    return record

async def api_key_auth_middleware(request: Request, call_next):
    """FastAPI middleware that validates X-API-Key for protected routes.
    Routes can be excluded via request.url.path if needed.
    """
    # Example: exclude health and auth routes
    if request.url.path.startswith("/api/v1/health") or request.url.path.startswith("/api/v1/auth"):
        response = await call_next(request)
        return response
    api_key = get_api_key(request)
    validate_api_key(api_key)
    response = await call_next(request)
    return response
