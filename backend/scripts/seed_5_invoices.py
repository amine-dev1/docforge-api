"""
Génère 5 factures (une par template) pour AMINE SARL et les upload sur Google Drive.
"""
from decimal import Decimal
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.tenant import Enterprise
from app.models.crm import Client
from app.models.catalogue import Product, TaxRate
from app.models.document import Document, DocumentLine, DocumentSequence
from app.services.pdf_service import generate_pdf
from app.services.drive_service import DriveService

CREDENTIALS_JSON = "google_drive_oauth.json"
PARENT_FOLDER_ID = "1xcdZgE1b8yHDlHapC9ns8MegEKeTZM9a"

TEMPLATES = ["minimal", "corporate", "creative", "dark", "swiss"]

# 5 sets de produits différents pour varier les factures
PRODUCT_SETS = [
    [("MacBook Pro 14 M3", 24500, 1), ("Dell UltraSharp 27 Monitor", 5800, 2)],
    [("Ergonomic Office Chair", 3200, 4), ("Standing Desk Pro", 4500, 2), ("Meeting Table (8 seats)", 12000, 1)],
    [("Cloud Hosting Monthly", 500, 3), ("IT Support Package", 2500, 1)],
    [("Logitech MX Master 3S", 1100, 5), ("Cisco Network Switch 24-Port", 8500, 1)],
    [("Custom Software Dev (Hour)", 650, 10), ("Cloud Hosting Monthly", 500, 2), ("IT Support Package", 2500, 1)],
]

def get_or_create_seq(db, ent_id):
    seq = db.query(DocumentSequence).filter(
        DocumentSequence.enterprise_id == ent_id,
        DocumentSequence.doc_type == "invoice",
        DocumentSequence.year == datetime.now().year
    ).first()
    if not seq:
        seq = DocumentSequence(enterprise_id=ent_id, doc_type="invoice",
                               year=datetime.now().year, last_seq=0)
        db.add(seq)
        db.flush()
    return seq


def seed_invoices():
    db = SessionLocal()
    drive = DriveService(CREDENTIALS_JSON, PARENT_FOLDER_ID)

    try:
        ent = db.query(Enterprise).filter(Enterprise.slug == 'amine-sarl').first()
        client = db.query(Client).filter(Client.enterprise_id == ent.id).first()
        tax = db.query(TaxRate).filter(TaxRate.enterprise_id == ent.id, TaxRate.is_default == True).first()

        if not client:
            print("Aucun client trouvé pour AMINE SARL.")
            return

        for idx, template_name in enumerate(TEMPLATES):
            print(f"\n[{idx+1}/5] Template : {template_name.upper()}")

            # 1. Numéro de facture
            seq = get_or_create_seq(db, ent.id)
            seq.last_seq += 1
            number = f"FAC-{datetime.now().year}-{seq.last_seq:04d}"

            # 2. Créer le document en DB
            doc = Document(
                enterprise_id=ent.id,
                client_id=client.id,
                type="invoice",
                number=number,
                status="draft",
                issued_at=datetime.now(timezone.utc),
                due_at=datetime.now(timezone.utc) + timedelta(days=30),
                currency="MAD",
                notes=f"Facture générée avec le template {template_name}."
            )
            db.add(doc)
            db.flush()

            # 3. Ajouter les lignes
            products_data = PRODUCT_SETS[idx]
            subtotal = Decimal("0")
            total_tax = Decimal("0")

            for pos, (prod_name, price, qty) in enumerate(products_data):
                price_d = Decimal(str(price))
                qty_d = Decimal(str(qty))
                line_ht = price_d * qty_d
                tax_amount = line_ht * (tax.rate / 100) if tax else Decimal("0")

                line = DocumentLine(
                    document_id=doc.id,
                    description=prod_name,
                    quantity=qty_d,
                    unit_price_ht=price_d,
                    tax_rate_value=tax.rate if tax else 0,
                    line_total_ht=line_ht,
                    tax_amount=tax_amount,
                    line_total_ttc=line_ht + tax_amount,
                    position=pos,
                )
                db.add(line)
                subtotal += line_ht
                total_tax += tax_amount

            doc.subtotal_ht = subtotal
            doc.total_tax = total_tax
            doc.total_ttc = subtotal + total_tax
            doc.amount_due = doc.total_ttc
            db.flush()

            # Reload lines
            doc_lines = db.query(DocumentLine).filter(
                DocumentLine.document_id == doc.id
            ).order_by(DocumentLine.position).all()

            # 4. Générer le PDF
            print(f"   Génération PDF ({template_name})...")
            pdf_bytes = generate_pdf(doc, ent, client, doc_lines, template_name=template_name)
            print(f"   PDF : {len(pdf_bytes)} bytes")

            # 5. Upload Google Drive
            print(f"   Upload Drive...")
            filename = f"{number}_{template_name}.pdf"
            result = drive.upload_file(pdf_bytes, filename, "application/pdf")

            # 6. Stocker le lien Drive dans le document
            doc.pdf_url = result.get("webViewLink")
            doc.pdf_key = result.get("id")
            db.commit()

            print(f"   OK  {number} | Total TTC : {doc.total_ttc} MAD")
            print(f"   URL {result.get('webViewLink')}")

        print("\n\n5/5 factures creees et uploadees avec succes !")

    except Exception as e:
        db.rollback()
        import traceback
        traceback.print_exc()
        print(f"\nErreur : {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_invoices()
