"""
Nettoyage : Supprime tous les fichiers du dossier Google Drive.
"""
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive']
TOKEN_PATH = "drive_token.json"
PARENT_FOLDER_ID = "1xcdZgE1b8yHDlHapC9ns8MegEKeTZM9a"

def cleanup_drive():
    if not os.path.exists(TOKEN_PATH):
        print("Erreur : Aucun token trouvé. Autorisez d'abord l'application.")
        return

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    service = build('drive', 'v3', credentials=creds)

    # 1. Lister tous les fichiers dans le dossier parent et ses sous-dossiers (comme 'invoices')
    # On cherche les fichiers dont le parent est le dossier de base OU le dossier 'invoices'
    
    # Trouver le dossier 'invoices' d'abord
    query_folder = f"name = 'invoices' and '{PARENT_FOLDER_ID}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    res_folder = service.files().list(q=query_folder, fields="files(id)").execute()
    folders = res_folder.get('files', [])
    
    folder_ids = [PARENT_FOLDER_ID]
    if folders:
        folder_ids.append(folders[0]['id'])
        print(f"Dossier 'invoices' trouvé : {folders[0]['id']}")

    for fid in folder_ids:
        print(f"\nNettoyage du dossier {fid}...")
        query = f"'{fid}' in parents and mimeType != 'application/vnd.google-apps.folder' and trashed = false"
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print("Aucun fichier trouvé.")
            continue

        for item in items:
            print(f"Suppression de : {item['name']} ({item['id']})")
            service.files().delete(fileId=item['id']).execute()
    
    print("\n✅ Nettoyage terminé.")

if __name__ == "__main__":
    cleanup_drive()
