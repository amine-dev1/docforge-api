from decimal import Decimal

import stripe
from fastapi import HTTPException


ZERO_DECIMAL = set('bif clp djf gnf jpy kmf krw mga pyg rwf vnd vuv xaf xof xpf'.split())
THREE_DECIMAL = set('bhd jod kwd omr tnd'.split())


def currency_factor(currency: str) -> int:
    currency = currency.lower()
    return 1 if currency in ZERO_DECIMAL else 1000 if currency in THREE_DECIMAL else 100


def minor_amount(amount, currency: str) -> int:
    value = Decimal(str(amount)) * currency_factor(currency)
    if value != value.to_integral_value() or (currency.lower() in {'isk', 'ugx'} and value % 100):
        raise HTTPException(400, 'Montant incompatible avec la devise Stripe.')
    return int(value)


def stripe_call(operation, **kwargs):
    # Never expose provider exceptions: they can contain the supplied secret key.
    try:
        return operation(**kwargs)
    except (stripe.AuthenticationError, stripe.PermissionError):
        raise HTTPException(400, 'Clé Stripe invalide ou permissions insuffisantes.') from None
    except stripe.InvalidRequestError:
        raise HTTPException(400, 'Stripe a refusé la demande. Vérifiez le montant, la devise et la configuration du compte.') from None
    except stripe.StripeError:
        raise HTTPException(502, 'Stripe est temporairement indisponible. Réessayez plus tard.') from None


def require_stripe(enterprise):
    if not enterprise.stripe_secret_key:
        raise HTTPException(400, 'Stripe non connecté')
    return enterprise.stripe_secret_key


def create_checkout(doc, enterprise):
    key = require_stripe(enterprise)
    if doc.amount_due <= 0:
        raise HTTPException(400, 'Facture déjà payée')
    if doc.status == 'cancelled':
        raise HTTPException(400, 'Cette facture est annulée.')
    base_url = f'http://localhost:5173/invoices/{doc.id}'
    session = stripe_call(
        stripe.checkout.Session.create, api_key=key, mode='payment',
        line_items=[{'price_data': {
            'currency': doc.currency.lower(),
            'unit_amount': minor_amount(doc.amount_due, doc.currency),
            'product_data': {'name': f'Facture {doc.number}'},
        }, 'quantity': 1}],
        client_reference_id=str(doc.id),
        metadata={'enterprise_id': str(enterprise.id), 'document_id': str(doc.id)},
        success_url=base_url + '?payment=success',
        cancel_url=base_url + '?payment=cancelled',
    )
    return {'url': session.url}
