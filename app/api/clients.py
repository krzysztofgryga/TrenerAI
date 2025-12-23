"""
Clients API router - JSON storage.
"""
from typing import List
from fastapi import APIRouter, HTTPException

from app.schemas import Client
from app.storage import load_clients, save_clients

router = APIRouter(tags=["Clients"])


@router.get("/clients")
def get_clients() -> List[dict]:
    """Get all clients."""
    return load_clients()


@router.post("/clients")
def add_client(client: Client) -> dict:
    """Add a new client."""
    clients = load_clients()
    clients.append(client.model_dump())
    save_clients(clients)
    return {"status": "ok", "client": client.model_dump()}


@router.put("/clients/{client_id}")
def update_client(client_id: str, client: Client) -> dict:
    """Update an existing client."""
    clients = load_clients()
    for i, c in enumerate(clients):
        if c["id"] == client_id:
            clients[i] = client.model_dump()
            save_clients(clients)
            return {"status": "ok", "client": client.model_dump()}
    raise HTTPException(status_code=404, detail="Client not found")


@router.delete("/clients/{client_id}")
def delete_client(client_id: str) -> dict:
    """Delete a client."""
    clients = load_clients()
    clients = [c for c in clients if c["id"] != client_id]
    save_clients(clients)
    return {"status": "ok"}
