"""Per-request credentials: the installed Resend SDK uses a global API key."""
import requests
from fastapi import HTTPException


def validate_resend_key(key: str):
    try:
        response = requests.get('https://api.resend.com/domains',
                                headers={'Authorization': f'Bearer {key}'}, timeout=15)
    except requests.RequestException:
        raise HTTPException(502, 'Resend est temporairement indisponible.') from None
    if response.status_code == 200:
        return
    # A sending-only key is authenticated but cannot list domains. Accept only
    # Resend's explicit restricted_api_key response, never an arbitrary 401/403.
    # This validates credentials without sending mail; domain/from authorization
    # is still checked by Resend at send time.
    try:
        name = response.json().get('name')
    except (ValueError, AttributeError):
        name = None
    if response.status_code in (401, 403) and name == 'restricted_api_key':
        return
    if response.status_code in (400, 401, 403, 422):
        raise HTTPException(400, 'Clé API Resend invalide ou permissions insuffisantes.')
    raise HTTPException(502, 'Resend est temporairement indisponible.')


def send_email(key: str, payload: dict):
    response = requests.post('https://api.resend.com/emails',
                             headers={'Authorization': f'Bearer {key}'},
                             json=payload, timeout=30)
    response.raise_for_status()
    return response.json()
