from fastapi import APIRouter

router = APIRouter(prefix="/tenant", tags=["Tenant"])

@router.get("/profile")
async def get_profile():
    # TODO: Profil + branding
    return {"message": "Endpoint non implémenté"}

@router.put("/profile")
async def update_profile():
    # TODO: Modifier infos + couleurs
    return {"message": "Endpoint non implémenté"}

@router.post("/logo")
async def upload_logo():
    # TODO: Upload logo (PNG/SVG, max 2MB)
    return {"message": "Endpoint non implémenté"}

@router.get("/api-keys")
async def list_api_keys():
    # TODO: Lister les clés API
    return {"message": "Endpoint non implémenté"}

@router.post("/api-keys")
async def create_api_key():
    # TODO: Créer une nouvelle clé
    return {"message": "Endpoint non implémenté"}

@router.delete("/api-keys/{id}")
async def revoke_api_key(id: str):
    # TODO: Révoquer une clé
    return {"message": "Endpoint non implémenté"}
