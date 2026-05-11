import io
import os
from typing import Dict
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']


def _get_token_path() -> str:
    try:
        from app.core.config import settings
        return settings.GOOGLE_DRIVE_TOKEN_PATH
    except Exception:
        return "drive_token.json"


class DriveService:
    def __init__(self, credentials_path: str, parent_folder_id: str):
        self.parent_id = parent_folder_id
        self.creds = self._get_credentials(credentials_path)
        self.service = build('drive', 'v3', credentials=self.creds)

    def _get_credentials(self, credentials_path: str) -> Credentials:
        creds = None
        token_path = _get_token_path()

        # 1. Charger le token mis en cache
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)

        # 2. Rafraîchir si expiré
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())

        # 3. Flux OAuth complet si pas de token valide
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            # Sauvegarder pour les prochaines exécutions
            with open(token_path, 'w') as f:
                f.write(creds.to_json())

        return creds

    def upload_file(self, file_content: bytes, filename: str, content_type: str) -> Dict:
        """Upload un fichier dans le dossier parent configuré."""
        file_metadata = {
            'name': filename,
            'parents': [self.parent_id]
        }

        fh = io.BytesIO(file_content)
        media = MediaIoBaseUpload(fh, mimetype=content_type, resumable=True)

        uploaded = self.service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, webViewLink',
        ).execute()

        return uploaded
