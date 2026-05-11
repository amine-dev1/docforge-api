import uuid
import secrets
import hashlib
import bcrypt
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.tenant import Enterprise
from app.models.user import User, UserRole
from app.models.api_key import APIKey

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()

def main():
    db = SessionLocal()
    now = datetime.now(timezone.utc)
    
    try:
        # Create a test enterprise
        ent = Enterprise(
            short_id=f"T{secrets.randbelow(1000) + 1000}", # Random ID to avoid collision
            slug=f"regular-test-{secrets.token_hex(4)}",
            legal_name="Regular User Test Corp",
            is_active=True
        )
        db.add(ent)
        db.flush()
        
        # Create a REGULAR user
        user = User(
            enterprise_id=ent.id,
            first_name="Regular",
            last_name="User",
            email=f"regular_{secrets.token_hex(4)}@test.com",
            hashed_password=hash_password("password123"),
            status="active",
            role=UserRole.regular.value # Explicitly set to regular
        )
        db.add(user)
        db.flush()
        
        # Create API Key
        plaintext = f"regular_{secrets.token_urlsafe(32)}"
        key_hash = hashlib.sha256(plaintext.encode()).hexdigest()
        
        api_key = APIKey(
            enterprise_id=ent.id,
            created_by=user.id,
            name="Regular Test Key",
            key_hash=key_hash,
            key_preview=plaintext[:8],
            is_active=True
        )
        db.add(api_key)
        
        db.commit()
        
        print("\n" + "="*50)
        print("SUCCESSFULLY CREATED TEST DATA")
        print("="*50)
        print(f"Tenant ID  : {ent.id}")
        print(f"Tenant Slug: {ent.slug}")
        print(f"User Email : {user.email}")
        print(f"User Role  : {user.role.value}")
        print(f"API KEY    : {plaintext}")
        print("="*50)
        print("Test this key in Swagger. Only /api/v1/tenant/me should work.")
        print("All other /tenant endpoints should return 403 Forbidden.")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
