from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register():
    # TODO: Créer compte + tenant
    return {"message": "Endpoint non implémenté"}

@router.post("/login")
async def login():
    # TODO: Email/password → access + refresh tokens
    return {"message": "Endpoint non implémenté"}

@router.post("/refresh")
async def refresh():
    # TODO: Nouveau access token via refresh
    return {"message": "Endpoint non implémenté"}

@router.post("/logout")
async def logout():
    # TODO: Blacklist refresh token (Redis)
    return {"message": "Endpoint non implémenté"}
