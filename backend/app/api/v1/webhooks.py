from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tenant import Enterprise
from app.models.document import Document
from app.models.finance import Payment, PaymentAllocation
from app.services.stripe_service import currency_factor

router = APIRouter(prefix='/webhooks', tags=['Webhooks'])


def process_stripe_webhook(enterprise_id: UUID, payload: bytes, signature: str, db: Session):
    enterprise = db.query(Enterprise).filter(Enterprise.id == enterprise_id).first()
    if not enterprise:
        raise HTTPException(404, 'Entreprise introuvable')
    if not enterprise.stripe_webhook_secret:
        raise HTTPException(400, 'Webhook Stripe non configuré pour cette entreprise')
    try:
        event = stripe.Webhook.construct_event(payload, signature, enterprise.stripe_webhook_secret).to_dict()
    except (ValueError, stripe.SignatureVerificationError):
        raise HTTPException(400, 'Signature Stripe invalide') from None

    ok = {'received': True}
    # Delayed payment methods can complete Checkout before funds are received.
    if event.get('type') not in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
        return ok
    session = event.get('data', {}).get('object', {})
    if session.get('payment_status') != 'paid' or session.get('mode') != 'payment':
        return ok
    metadata = session.get('metadata') or {}
    if metadata.get('enterprise_id') != str(enterprise_id):
        return ok
    try:
        document_id = UUID(metadata.get('document_id', ''))
    except (ValueError, TypeError, AttributeError):
        return ok
    reference = session.get('id')
    if not isinstance(reference, str) or not reference.startswith('cs_') or len(reference) > 255:
        return ok
    # Serialize retries for the entire tenant, including simultaneous events.
    db.query(Enterprise).filter(Enterprise.id == enterprise_id).with_for_update().one()
    references = [reference]
    if isinstance(session.get('payment_intent'), str):
        references.append(session['payment_intent'])
    if db.query(Payment).filter(Payment.enterprise_id == enterprise_id,
                                Payment.reference.in_(references)).first():
        return ok
    doc = db.query(Document).filter(Document.id == document_id,
                                    Document.enterprise_id == enterprise_id,
                                    Document.type == 'invoice', Document.is_deleted == False
                                    ).with_for_update().first()
    if not doc or doc.status == 'cancelled' or doc.amount_due <= 0:
        return ok
    currency = session.get('currency', '').upper()
    total = session.get('amount_total')
    if currency != doc.currency.upper() or type(total) is not int or total <= 0:
        return ok
    # Same minor-unit conversion as Checkout (100 for MAD/EUR; JPY is 1).
    amount = min(Decimal(total) / currency_factor(currency), doc.amount_due)
    if amount != amount.quantize(Decimal('0.01')):
        return ok  # The accounting schema stores two decimal places.
    payment = Payment(enterprise_id=enterprise_id, client_id=doc.client_id,
                      reference=reference, method='card', amount=amount, currency=currency,
                      payment_date=datetime.now(timezone.utc).date(),
                      amount_allocated=amount, amount_remaining=Decimal(0), status='confirmed')
    db.add(payment)
    db.flush()
    db.add(PaymentAllocation(payment_id=payment.id, document_id=doc.id, amount_allocated=amount))
    # Keep the same allocation and status rules as POST /payments/.
    doc.amount_paid = (doc.amount_paid or Decimal(0)) + amount
    doc.amount_due = doc.total_ttc - doc.amount_paid
    if doc.amount_due <= 0:
        doc.status = 'paid'
    elif doc.amount_paid > 0:
        doc.status = 'partially_paid'
    db.commit()
    return ok


@router.post('/stripe/{enterprise_id}')
async def stripe_webhook(enterprise_id: UUID, request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    return await run_in_threadpool(process_stripe_webhook, enterprise_id, payload,
                                  request.headers.get('Stripe-Signature', ''), db)
