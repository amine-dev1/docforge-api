
import json
import secrets
import hashlib
import urllib.request
from uuid import UUID
from decimal import Decimal

# Internal imports to access DB and Models
from app.core.database import SessionLocal
from app.models.enterprise import Enterprise
from app.models.api_key import ApiKey
from app.models.user import User

def setup_api_key():
    db = SessionLocal()
    try:
        # Get the first enterprise
        ent = db.query(Enterprise).first()
        if not ent:
            print("No enterprise found. Please run seed_tenants.py first.")
            return None
        
        # Get the admin user for this enterprise
        user = db.query(User).filter(User.enterprise_id == ent.id).first()
        
        # Create a fresh API Key
        plaintext = f"demo_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        
        demo_key = ApiKey(
            enterprise_id=ent.id,
            created_by=user.id,
            name="Demo Script Key",
            key_hash=key_hash,
            key_preview=plaintext[:8],
            is_active=True
        )
        db.add(demo_key)
        db.commit()
        print(f"Created temporary API Key: {plaintext}")
        return plaintext
    finally:
        db.close()

def call_api(path, method, api_key, data=None):
    url = f"http://localhost:8000/api/v1{path}"
    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json"
    }
    
    body = json.dumps(data).encode('utf-8') if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        print(f"Error calling {path}: {e.read().decode()}")
        return None

def main():
    api_key = setup_api_key()
    if not api_key:
        return

    # 1. Create a Client
    print("\n--- Creating Client ---")
    client_data = {
        "legal_name": "Global Solutions SARL",
        "trade_name": "Global Solutions",
        "email": "procurement@globalsolutions.ma",
        "address_city": "Casablanca",
        "ice": "009988776655443",
        "contacts": [
            {
                "first_name": "Karim",
                "last_name": "Alami",
                "email": "k.alami@globalsolutions.ma",
                "is_primary": True
            }
        ]
    }
    client_res = call_api("/clients/", "POST", api_key, client_data)
    if not client_res: return
    
    client_id = client_res["data"]["id"]
    print(f"Created Client: {client_res['data']['legal_name']} (ID: {client_id})")

    # 2. Create an Invoice
    print("\n--- Creating Invoice ---")
    invoice_data = {
        "type": "invoice",
        "client_id": client_id,
        "currency": "MAD",
        "notes": "Thank you for your business!",
        "lines": [
            {
                "description": "MacBook Pro M3 14\"",
                "quantity": 1,
                "unit_price_ht": 22000.00,
                "tax_rate_value": 20.0
            },
            {
                "description": "Dell UltraSharp 27 Monitor",
                "quantity": 2,
                "unit_price_ht": 4500.00,
                "tax_rate_value": 20.0
            }
        ]
    }
    invoice_res = call_api("/documents/", "POST", api_key, invoice_data)
    if not invoice_res: return
    
    print(f"Created Invoice: {invoice_res['data']['number']}")
    print(f"Total TTC: {invoice_res['data']['total_ttc']} MAD")
    print(f"Status: {invoice_res['data']['status']}")

if __name__ == "__main__":
    main()
