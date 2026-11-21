"""X-24/X-25: additive schema migration and AMINE SARL-only Resend transfer."""
from pathlib import Path

import psycopg2
from dotenv import dotenv_values


def main():
    config = dotenv_values(Path(__file__).resolve().parents[1] / '.env')
    target = '91385743-2550-4ddf-946c-860ae2569304'
    with psycopg2.connect(config['DATABASE_URL']) as connection:
        with connection.cursor() as cursor:
            cursor.execute('SELECT id, legal_name, stripe_secret_key, stripe_publishable_key FROM enterprises WHERE id = %s FOR UPDATE', (target,))
            before = cursor.fetchone()
            if not before or str(before[0]) != target or before[1] != 'AMINE SARL':
                raise RuntimeError('Entreprise cible non conforme : migration annulée')
            for column in ('resend_api_key', 'resend_from_email', 'stripe_webhook_secret'):
                cursor.execute(f'ALTER TABLE enterprises ADD COLUMN IF NOT EXISTS {column} VARCHAR(255)')
            cursor.execute('ALTER TABLE payments ALTER COLUMN reference TYPE VARCHAR(255)')
            key = (config.get('RESEND_API_KEY') or '').strip()
            sender = (config.get('RESEND_FROM_EMAIL') or '').strip()
            if not key or not sender:
                raise RuntimeError('Configuration Resend source manquante : transaction annulée')
            # Reruns never overwrite a connection subsequently changed in the UI.
            cursor.execute('UPDATE enterprises SET resend_api_key = %s, resend_from_email = %s WHERE id = %s AND resend_api_key IS NULL', (key, sender, target))
            changed = cursor.rowcount
            cursor.execute('SELECT stripe_secret_key, stripe_publishable_key, resend_api_key, resend_from_email FROM enterprises WHERE id = %s', (target,))
            after = cursor.fetchone()
            assert after[:2] == before[2:], 'Configuration Stripe modifiée'
            assert after[2] and after[3], 'Configuration Resend absente'
    print(f'Migration validée : AMINE SARL ; {changed} connexion Resend transférée ; clés Stripe inchangées.')


if __name__ == '__main__':
    main()
