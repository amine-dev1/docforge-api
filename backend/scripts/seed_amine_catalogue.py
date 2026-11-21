
import uuid
from decimal import Decimal
from app.core.database import SessionLocal
from app.models.tenant import Enterprise
from app.models.user import User
from app.models.catalogue import UnitOfMeasure, TaxRate, ProductCategory, Product

def seed_amine_catalogue():
    db = SessionLocal()
    try:
        # 1. Find Enterprise and User
        ent = db.query(Enterprise).filter(Enterprise.slug == 'amine-sarl').first()
        user = db.query(User).filter(User.email == 'elidrissiamine74@gmail.com').first()

        if not ent or not user:
            print("Enterprise 'amine-sarl' or user not found. Please ensure they exist.")
            return

        ent_id = ent.id
        user_id = user.id

        # 2. Units of Measure
        print("Checking/Creating Units...")
        def get_or_create_uom(name, symbol, is_default):
            obj = db.query(UnitOfMeasure).filter(UnitOfMeasure.enterprise_id == ent_id, UnitOfMeasure.symbol == symbol).first()
            if not obj:
                obj = UnitOfMeasure(enterprise_id=ent_id, name=name, symbol=symbol, is_default=is_default)
                db.add(obj)
                db.flush()
            return obj

        uom_pcs = get_or_create_uom("Pieces", "pcs", True)
        uom_kg = get_or_create_uom("Kilogram", "kg", False)
        uom_box = get_or_create_uom("Box", "box", False)

        # 3. Tax Rates
        print("Checking/Creating Tax Rates...")
        tax_20 = db.query(TaxRate).filter(TaxRate.enterprise_id == ent_id, TaxRate.rate == 20).first()
        if not tax_20:
            tax_20 = TaxRate(enterprise_id=ent_id, name="TVA 20%", label="20%", rate=Decimal("20.00"), is_default=True)
            db.add(tax_20)
            db.flush()

        # 4. Product Categories
        print("Checking/Creating Categories...")
        def get_or_create_cat(name, code):
            obj = db.query(ProductCategory).filter(ProductCategory.enterprise_id == ent_id, ProductCategory.code == code).first()
            if not obj:
                obj = ProductCategory(enterprise_id=ent_id, name=name, code=code)
                db.add(obj)
                db.flush()
            return obj

        cat_elec = get_or_create_cat("Electronics", "ELEC")
        cat_furn = get_or_create_cat("Office Furniture", "FURN")
        cat_serv = get_or_create_cat("Digital Services", "SERV")

        # 5. Products (10 items)
        print("Creating Products...")
        products_data = [
            # Electronics
            {"name": "MacBook Pro 14 M3", "code": "LAP-001", "cat": cat_elec, "price": 24500, "uom": uom_pcs},
            {"name": "Dell UltraSharp 27 Monitor", "code": "MON-001", "cat": cat_elec, "price": 5800, "uom": uom_pcs},
            {"name": "Logitech MX Master 3S", "code": "ACC-001", "cat": cat_elec, "price": 1100, "uom": uom_pcs},
            {"name": "Cisco Network Switch 24-Port", "code": "NET-001", "cat": cat_elec, "price": 8500, "uom": uom_pcs},
            
            # Furniture
            {"name": "Ergonomic Office Chair", "code": "FUR-001", "cat": cat_furn, "price": 3200, "uom": uom_pcs},
            {"name": "Standing Desk Pro", "code": "FUR-002", "cat": cat_furn, "price": 4500, "uom": uom_pcs},
            {"name": "Meeting Table (8 seats)", "code": "FUR-003", "cat": cat_furn, "price": 12000, "uom": uom_pcs},
            
            # Services
            {"name": "Cloud Hosting Monthly", "code": "SRV-001", "cat": cat_serv, "price": 500, "uom": uom_pcs},
            {"name": "IT Support Package", "code": "SRV-002", "cat": cat_serv, "price": 2500, "uom": uom_pcs},
            {"name": "Custom Software Dev (Hour)", "code": "SRV-003", "cat": cat_serv, "price": 650, "uom": uom_pcs},
        ]

        for p in products_data:
            existing_prod = db.query(Product).filter(Product.enterprise_id == ent_id, Product.code == p["code"]).first()
            if not existing_prod:
                prod = Product(
                    enterprise_id=ent_id,
                    category_id=p["cat"].id,
                    unit_id=p["uom"].id,
                    tax_rate_id=tax_20.id,
                    name=p["name"],
                    code=p["code"],
                    sale_price_ht=Decimal(str(p["price"])),
                    created_by=user_id,
                    is_active=True
                )
                db.add(prod)

        db.commit()
        print(f"Successfully seeded catalogue for {ent.legal_name}!")

    except Exception as e:
        db.rollback()
        print(f"Error during seeding: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_amine_catalogue()
