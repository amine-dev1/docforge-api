import uuid
import os
from datetime import datetime, timedelta

import bcrypt

from app.core.database import SessionLocal, engine
from app.models.tenant import Enterprise
from app.models.user import User, RefreshToken
from app.models.catalogue import UnitOfMeasure, TaxRate, ProductCategory, Product
from app.models.crm import Client, Supplier

# Password hashing helper
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_initial_data():
    db = SessionLocal()
    try:
        # 1. Enterprise
        enterprise = db.query(Enterprise).filter(Enterprise.slug == "amine-sarl").first()
        if not enterprise:
            enterprise = Enterprise(
                id=uuid.uuid4(),
                slug="amine-sarl",
                legal_name="AMINE SARL",
                trade_name="AMINE SARL",
                email_general="elidrissiamine74@gmail.com",
                ice="123456789012345",
                rc="123456",
                if_number="78901234",
                address_street="Avenue Mohammed V",
                address_city="Casablanca",
                address_country="MA",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(enterprise)
            db.commit()
            db.refresh(enterprise)
            print("Enterprise created.")
        else:
            print("Enterprise already exists.")

        # 2. User
        user = db.query(User).filter(User.email == "elidrissiamine74@gmail.com").first()
        if not user:
            hashed_pw = hash_password("elidrissi2002")
            user = User(
                id=uuid.uuid4(),
                enterprise_id=enterprise.id,
                first_name="Elidrissi",
                last_name="Amin",
                email="elidrissiamine74@gmail.com",
                hashed_password=hashed_pw,
                status="active",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print("User created.")
        else:
            print("User already exists.")

        # 3. Units of Measure
        units = [
            {"name": "Unité", "symbol": "U", "is_default": True},
            {"name": "Heure", "symbol": "h", "is_default": False},
            {"name": "Jour", "symbol": "j", "is_default": False},
            {"name": "Mois", "symbol": "m", "is_default": False},
        ]
        created_units = {}
        for u_data in units:
            unit = db.query(UnitOfMeasure).filter(
                UnitOfMeasure.enterprise_id == enterprise.id, 
                UnitOfMeasure.symbol == u_data["symbol"]
            ).first()
            if not unit:
                unit = UnitOfMeasure(enterprise_id=enterprise.id, **u_data)
                db.add(unit)
                db.flush()
            created_units[u_data["symbol"]] = unit
        db.commit()
        print("Units of measure seeded.")

        # 4. Tax Rates
        taxes = [
            {"name": "TVA 20%", "label": "TVA 20%", "rate": 20.00, "is_default": True},
            {"name": "TVA 14%", "label": "TVA 14%", "rate": 14.00, "is_default": False},
            {"name": "TVA 10%", "label": "TVA 10%", "rate": 10.00, "is_default": False},
            {"name": "Exonéré", "label": "Exo", "rate": 0.00, "is_default": False},
        ]
        created_taxes = {}
        for t_data in taxes:
            tax = db.query(TaxRate).filter(
                TaxRate.enterprise_id == enterprise.id, 
                TaxRate.rate == t_data["rate"]
            ).first()
            if not tax:
                tax = TaxRate(enterprise_id=enterprise.id, **t_data)
                db.add(tax)
                db.flush()
            created_taxes[t_data["rate"]] = tax
        db.commit()
        print("Tax rates seeded.")

        # 5. Product Categories
        categories = [
            {"name": "Services Informatiques", "code": "SERV-IT"},
            {"name": "Matériel", "code": "MAT"},
            {"name": "Licences Logiciels", "code": "LIC"},
        ]
        created_cats = {}
        for c_data in categories:
            cat = db.query(ProductCategory).filter(
                ProductCategory.enterprise_id == enterprise.id, 
                ProductCategory.code == c_data["code"]
            ).first()
            if not cat:
                cat = ProductCategory(enterprise_id=enterprise.id, **c_data)
                db.add(cat)
                db.flush()
            created_cats[c_data["code"]] = cat
        db.commit()
        print("Product categories seeded.")

        # 6. Products
        products = [
            {
                "name": "Développement Web Senior", 
                "code": "DEV-SR", 
                "category_id": created_cats["SERV-IT"].id,
                "unit_id": created_units["h"].id,
                "tax_rate_id": created_taxes[20.00].id,
                "sale_price_ht": 800.00,
                "type": "service"
            },
            {
                "name": "Audit de Sécurité", 
                "code": "AUDIT-SEC", 
                "category_id": created_cats["SERV-IT"].id,
                "unit_id": created_units["j"].id,
                "tax_rate_id": created_taxes[20.00].id,
                "sale_price_ht": 6500.00,
                "type": "service"
            },
            {
                "name": "MacBook Pro 16\"", 
                "code": "MBP-16", 
                "category_id": created_cats["MAT"].id,
                "unit_id": created_units["U"].id,
                "tax_rate_id": created_taxes[20.00].id,
                "sale_price_ht": 28000.00,
                "type": "product"
            }
        ]
        for p_data in products:
            prod = db.query(Product).filter(
                Product.enterprise_id == enterprise.id, 
                Product.code == p_data["code"]
            ).first()
            if not prod:
                prod = Product(enterprise_id=enterprise.id, created_by=user.id, **p_data)
                db.add(prod)
        db.commit()
        print("Products seeded.")

        # 7. Clients
        clients = [
            {
                "legal_name": "TECH SOLUTIONS SARL", 
                "code": "CLI001", 
                "email": "contact@techsolutions.ma",
                "address_street": "Boulevard Zerktouni",
                "address_city": "Casablanca",
                "ice": "001234567890011"
            }
        ]
        for cl_data in clients:
            client = db.query(Client).filter(
                Client.enterprise_id == enterprise.id, 
                Client.legal_name == cl_data["legal_name"]
            ).first()
            if not client:
                client = Client(enterprise_id=enterprise.id, created_by=user.id, **cl_data)
                db.add(client)
        db.commit()
        print("Clients seeded.")

        # 8. Suppliers
        suppliers = [
            {
                "legal_name": "CLOUD PROVIDER X", 
                "code": "SUP001", 
                "email": "billing@cloudx.com",
                "address_street": "Silicon Valley",
                "address_city": "San Francisco",
                "address_country": "US"
            }
        ]
        for s_data in suppliers:
            supplier = db.query(Supplier).filter(
                Supplier.enterprise_id == enterprise.id, 
                Supplier.legal_name == s_data["legal_name"]
            ).first()
            if not supplier:
                supplier = Supplier(enterprise_id=enterprise.id, created_by=user.id, **s_data)
                db.add(supplier)
        db.commit()
        print("Suppliers seeded.")

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    create_initial_data()

