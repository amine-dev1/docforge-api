from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.sql import text
from app.core.database import get_db

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Status API + DB + Redis + Storage
    """
    health_status = {
        "status": "healthy",
        "api": "up",
        "database": "down",
        "redis": "not_configured",
        "storage": "not_configured"
    }

    # Database check
    try:
        db.execute(text("SELECT 1"))
        health_status["database"] = "up"
    except Exception as e:
        health_status["database"] = f"error: {str(e)}"
        health_status["status"] = "unhealthy"

    # Note: Redis and Storage (MinIO) checks will be implemented later
    
    return health_status
