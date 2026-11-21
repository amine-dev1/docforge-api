
import uuid
from decimal import Decimal
from datetime import datetime, timezone
from app.core.database import SessionLocal
from app.models.tenant import Enterprise
from app.models.crm import Client
from app.models.catalogue import Product, TaxRate
from app.models.document import Document, DocumentLine, DocumentSequence

def create_quote_for_amine():
    db = SessionLocal()
    client_id = "82fb28e2-5617-4352-970e-b7140da320eb"
    
    try:
        # 1. Get Client and Enterprise
        client = db.query(Client).filter(Client.id == client_id).first()
        if not client:
            print(f"Error: Client {client_id} not found.")
            return

        ent_id = client.enterprise_id
        ent = db.query(Enterprise).filter(Enterprise.id == ent_id).first()

        # 2. Get some products
        products = db.query(Product).filter(Product.enterprise_id == ent_id).limit(2).all()
        if not products:
            print("Error: No products found for this tenant. Please seed products first.")
            return

        # 3. Get Tax Rate
        tax = db.query(TaxRate).filter(TaxRate.enterprise_id == ent_id, TaxRate.is_default == True).first()
        if not tax:
            tax = db.query(TaxRate).filter(TaxRate.enterprise_id == ent_id).first()

        # 4. Generate Quote Number
        # Use simple logic since we are in a script
        seq = db.query(DocumentSequence).filter(
            DocumentSequence.enterprise_id == ent_id,
            DocumentSequence.doc_type == "quote",
            DocumentSequence.year == datetime.now().year
        ).first()
        
        if not seq:
            seq = DocumentSequence(enterprise_id=ent_id, doc_type="quote", year=datetime.now().year, last_seq=0)
            db.add(seq)
            db.flush()
        
        seq.last_seq += 1
        quote_number = f"DEV-{datetime.now().year}-{seq.last_seq:04d}"

        # 5. Create Quote Document
        quote = Document(
            enterprise_id=ent_id,
            client_id=client.id,
            type="quote",
            number=quote_number,
            status="draft",
            issued_at=datetime.now(timezone.utc),
            currency="MAD",
            notes="Quote generated for testing purposes."
        )
        db.add(quote)
        db.flush()

        # 6. Add Lines
        total_ht = Decimal("0.00")
        total_tax = Decimal("0.00")

        for p in products:
            qty = Decimal("1.000")
            price = p.sale_price_ht or Decimal("100.00")
            line_ht = price * qty
            line_tva = (line_ht * (tax.rate / 100)) if tax else Decimal("0.00")
            
            line = DocumentLine(
                document_id=quote.id,
                product_id=p.id,
                description=p.name,
                quantity=qty,
                unit_price_ht=price,
                tax_rate_value=tax.rate if tax else 0,
                line_total_ht=line_ht,
                tax_amount=line_tva,
                line_total_ttc=line_ht + line_tva
            )
            db.add(line)
            total_ht += line_ht
            total_tax += line_tva

        # 7. Update Quote Totals
        quote.subtotal_ht = total_ht
        quote.total_tax = total_tax
        quote.total_ttc = total_ht + total_tax
        quote.amount_due = quote.total_ttc

        db.commit()
        print(f"SUCCESS: Created Quote {quote_number} for {client.legal_name}")
        print(f"Quote ID: {quote.id}")
        print(f"Total TTC: {quote.total_ttc} MAD")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    create_quote_for_amine()
