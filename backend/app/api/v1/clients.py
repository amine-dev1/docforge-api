from typing import List
from fastapi import APIRouter, Depends, HTTPException, Security, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.auth import get_current_enterprise, SecurityContext
from app.models.crm import Client, ClientContact
from app.schemas.crm import (
    ClientCreate, ClientUpdate, ClientOut,
    ClientContactCreate, ClientContactUpdate, ClientContactOut,
)
from app.schemas.response import StandardResponse

router = APIRouter(prefix="/clients", tags=["Clients"])


# ─────────────────────────────────────────────
# CLIENTS
# ─────────────────────────────────────────────

@router.get("/", response_model=StandardResponse[List[ClientOut]])
async def list_clients(
    page: int = 1,
    size: int = 20,
    is_active: bool = None,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all clients for the authenticated tenant."""
    query = db.query(Client).filter(Client.enterprise_id == ctx.enterprise.id)
    if is_active is not None:
        query = query.filter(Client.is_active == is_active)
    clients = query.offset((page - 1) * size).limit(size).all()
    return {"status": 200, "data": clients}


@router.post("/", response_model=StandardResponse[ClientOut], status_code=status.HTTP_201_CREATED)
async def create_client(
    client_in: ClientCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Create a new client for the authenticated tenant."""
    contacts_data = client_in.contacts or []
    client_data = client_in.model_dump(exclude={"contacts"})

    client = Client(**client_data, enterprise_id=ctx.enterprise.id, created_by=ctx.user.id)
    db.add(client)
    db.flush()  # get client.id

    for c in contacts_data:
        contact = ClientContact(**c.model_dump(), client_id=client.id)
        db.add(contact)

    db.commit()
    db.refresh(client)
    return {"status": 201, "data": client}


@router.get("/{client_id}", response_model=StandardResponse[ClientOut])
async def get_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Get a single client by ID."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"status": 200, "data": client}


@router.patch("/{client_id}", response_model=StandardResponse[ClientOut])
async def update_client(
    client_id: UUID,
    client_in: ClientUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Partially update a client."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    for field, value in client_in.model_dump(exclude_none=True).items():
        setattr(client, field, value)

    db.commit()
    db.refresh(client)
    return {"status": 200, "data": client}


@router.delete("/{client_id}", response_model=StandardResponse[dict])
async def delete_client(
    client_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Soft-delete a client (sets is_active=False)."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    client.is_active = False
    db.commit()
    return {"status": 200, "data": {"message": f"Client {client.legal_name} deactivated"}}


# ─────────────────────────────────────────────
# CLIENT CONTACTS (sub-resource)
# ─────────────────────────────────────────────

@router.get("/{client_id}/contacts", response_model=StandardResponse[List[ClientContactOut]])
async def list_client_contacts(
    client_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """List all contacts for a client."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"status": 200, "data": client.contacts}


@router.post("/{client_id}/contacts", response_model=StandardResponse[ClientContactOut], status_code=status.HTTP_201_CREATED)
async def add_client_contact(
    client_id: UUID,
    contact_in: ClientContactCreate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Add a contact to a client."""
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")

    contact = ClientContact(**contact_in.model_dump(), client_id=client_id)
    db.add(contact)
    db.commit()
    db.refresh(contact)
    return {"status": 201, "data": contact}


@router.patch("/{client_id}/contacts/{contact_id}", response_model=StandardResponse[ClientContactOut])
async def update_client_contact(
    client_id: UUID,
    contact_id: UUID,
    contact_in: ClientContactUpdate,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Update a contact."""
    contact = db.query(ClientContact).join(Client).filter(
        ClientContact.id == contact_id,
        ClientContact.client_id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for field, value in contact_in.model_dump(exclude_none=True).items():
        setattr(contact, field, value)

    db.commit()
    db.refresh(contact)
    return {"status": 200, "data": contact}


@router.delete("/{client_id}/contacts/{contact_id}", response_model=StandardResponse[dict])
async def delete_client_contact(
    client_id: UUID,
    contact_id: UUID,
    db: Session = Depends(get_db),
    ctx: SecurityContext = Security(get_current_enterprise),
):
    """Delete a contact permanently."""
    contact = db.query(ClientContact).join(Client).filter(
        ClientContact.id == contact_id,
        ClientContact.client_id == client_id,
        Client.enterprise_id == ctx.enterprise.id
    ).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"status": 200, "data": {"message": "Contact deleted"}}
