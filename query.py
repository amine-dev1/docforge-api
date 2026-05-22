import sys
import os

# Ensure the current directory is in the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.models.user import User
from app.models.tenant import Enterprise
from app.models.crm import Client

def get_clients_for_user_email(email: str):
    db = SessionLocal()
    try:
        # Find user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"No user found with email: {email}")
            return
        
        # Get enterprise
        enterprise_id = user.enterprise_id
        enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
        
        print(f"User found in Enterprise: {enterprise.name if enterprise else 'Unknown'} (ID: {enterprise_id})")
        
        # Get clients
        clients = db.query(Client).filter(Client.enterprise_id == enterprise_id).all()
        
        if not clients:
            print("No clients found for this enterprise.")
            return
            
        print("\nClients list:")
        for idx, client in enumerate(clients, 1):
            print(f"{idx}. {client.name} (Email: {client.email}, Phone: {client.phone})")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    get_clients_for_user_email("elidrissiamine74@gmail.com")
