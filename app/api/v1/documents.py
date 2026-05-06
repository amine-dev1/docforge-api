from fastapi import APIRouter

router = APIRouter(prefix="/documents", tags=["Documents"])

@router.post("/invoice")
async def create_invoice():
    # TODO: Générer facture
    return {"message": "Endpoint non implémenté"}

@router.post("/quote")
async def create_quote():
    # TODO: Générer devis
    return {"message": "Endpoint non implémenté"}

@router.post("/purchase-order")
async def create_purchase_order():
    # TODO: Bon de commande
    return {"message": "Endpoint non implémenté"}

@router.post("/delivery-note")
async def create_delivery_note():
    # TODO: Bon de livraison
    return {"message": "Endpoint non implémenté"}

@router.get("/")
async def list_documents():
    # TODO: Historique (pagination + filtres)
    return {"message": "Endpoint non implémenté"}

@router.get("/{id}")
async def get_document(id: str):
    # TODO: Détails d'un document
    return {"message": "Endpoint non implémenté"}

@router.get("/{id}/pdf")
async def get_document_pdf(id: str):
    # TODO: URL signée MinIO (expire 1h)
    return {"message": "Endpoint non implémenté"}

@router.delete("/{id}")
async def delete_document(id: str):
    # TODO: Supprimer (soft delete)
    return {"message": "Endpoint non implémenté"}
