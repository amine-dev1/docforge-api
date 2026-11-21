"""
Quick test: generate a PDF for the existing quote DEV-2026-0001 and upload to Google Drive.
"""
from app.core.database import SessionLocal
from app.models.document import Document, DocumentLine
from app.models.tenant import Enterprise
from app.models.crm import Client
from app.services.pdf_service import generate_pdf
from app.services.drive_service import DriveService

CREDENTIALS_JSON = "google_drive_oauth.json"
PARENT_FOLDER_ID = "1xcdZgE1b8yHDlHapC9ns8MegEKeTZM9a"

def test_pdf_flow():
    db = SessionLocal()
    try:
        # 1. Load the existing quote
        doc = db.query(Document).filter(Document.number == "DEV-2026-0001").first()
        if not doc:
            print("Quote DEV-2026-0001 not found.")
            return

        ent = db.query(Enterprise).filter(Enterprise.id == doc.enterprise_id).first()
        client = db.query(Client).filter(Client.id == doc.client_id).first() if doc.client_id else None
        lines = db.query(DocumentLine).filter(DocumentLine.document_id == doc.id).order_by(DocumentLine.position).all()

        print(f"Document: {doc.number} ({doc.type})")
        print(f"Enterprise: {ent.legal_name}")
        print(f"Client: {client.legal_name if client else 'N/A'}")
        print(f"Lines: {len(lines)}")

        # 2. Generate PDF
        print("Generating PDF...")
        pdf_bytes = generate_pdf(doc, ent, client, lines)
        print(f"PDF generated: {len(pdf_bytes)} bytes")

        # 3. Upload to Google Drive
        print("Uploading to Google Drive...")
        drive = DriveService(CREDENTIALS_JSON, PARENT_FOLDER_ID)
        result = drive.upload_file(pdf_bytes, f"{doc.number}.pdf", "application/pdf")

        # 4. Save Drive link back to document
        doc.pdf_url = result.get("webViewLink")
        doc.pdf_key = result.get("id")
        db.commit()

        print(f"\nSUCCESS!")
        print(f"Drive File ID: {result.get('id')}")
        print(f"Drive URL: {result.get('webViewLink')}")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    test_pdf_flow()
