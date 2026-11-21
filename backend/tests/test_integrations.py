import asyncio
import base64
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace as NS
import unittest
from unittest.mock import MagicMock, patch
from uuid import uuid4

import stripe
from fastapi import HTTPException
from app.api.v1.documents import send_document
from app.api.v1.invoices import invoice_checkout
from app.api.v1.tenant import connect_stripe, disconnect_stripe, stripe_dashboard, StripeConnect
from app.core.config import settings
from app.models.tenant import Enterprise
from app.schemas.tenant import EnterpriseOut
from app.services.stripe_service import create_checkout, minor_amount


class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.enterprise = NS(id=uuid4(), stripe_secret_key='sk_test_private', stripe_publishable_key='pk_test_public', legal_name='Entreprise', resend_api_key='re_tenant', resend_from_email='billing@example.com')
        self.ctx = NS(enterprise=self.enterprise)
        self.db = MagicMock()
        self.doc = NS(id=uuid4(), client_id=uuid4(), number='FAC-1', amount_due=Decimal('12.34'),
                      total_ttc=Decimal('24.68'), currency='MAD', status='draft', due_at=None, sent_at=None)

    def test_secret_is_not_serialized(self):
        now = datetime.now(timezone.utc)
        enterprise = Enterprise(short_id='T1', slug='test', legal_name='Test', stripe_secret_key='sk_test_NEVER_RETURN',
            resend_api_key='re_NEVER_RETURN', resend_from_email='billing@example.com', stripe_webhook_secret='whsec_NEVER_RETURN', stripe_publishable_key='pk_test_public', is_active=True, is_verified=False, created_at=now, updated_at=now)
        # SQLAlchemy server defaults are populated on persistence, not construction.
        for name, field in EnterpriseOut.model_fields.items():
            if getattr(enterprise, name, None) is None and field.default is not None and not field.is_required():
                setattr(enterprise, name, field.default)
        result = EnterpriseOut.model_validate(enterprise).model_dump_json()
        self.assertNotIn('NEVER_RETURN', result)
        self.assertNotIn('stripe_secret_key', result)
        self.assertIn('"stripe_connected":true', result)

    def test_invalid_key_does_not_persist_or_leak(self):
        with patch('stripe.Balance.retrieve', side_effect=stripe.AuthenticationError('secret sk_test_bad')):
            with self.assertRaises(HTTPException) as error:
                connect_stripe(StripeConnect(secret_key='sk_test_bad', publishable_key='pk_test_public'), self.db, self.ctx)
        self.assertEqual(error.exception.status_code, 400)
        self.assertNotIn('sk_test_bad', error.exception.detail)
        self.db.commit.assert_not_called()
        self.assertEqual(self.enterprise.stripe_secret_key, 'sk_test_private')

    def test_connect_disconnect(self):
        with patch('stripe.Balance.retrieve') as balance:
            connect_stripe(StripeConnect(secret_key='sk_test_new', publishable_key='pk_test_new'), self.db, self.ctx)
            balance.assert_called_once_with(api_key='sk_test_new')
        self.assertEqual(self.enterprise.stripe_secret_key, 'sk_test_new')
        disconnect_stripe(self.db, self.ctx)
        self.assertIsNone(self.enterprise.stripe_secret_key)
        self.assertIsNone(self.enterprise.stripe_publishable_key)

    def test_checkout_uses_due_and_tenant_key(self):
        with patch('stripe.checkout.Session.create', return_value=NS(url='https://checkout.stripe.com/test')) as create:
            self.assertEqual(create_checkout(self.doc, self.enterprise)['url'], 'https://checkout.stripe.com/test')
            args = create.call_args.kwargs
            self.assertEqual(args['api_key'], 'sk_test_private')
            self.assertEqual(args['line_items'][0]['price_data']['unit_amount'], 1234)
            self.assertIn('?payment=success', args['success_url'])
            self.assertEqual(args['metadata'], {'document_id': str(self.doc.id), 'enterprise_id': str(self.enterprise.id)})
        self.doc.amount_due = 0
        with self.assertRaises(HTTPException) as error:
            create_checkout(self.doc, self.enterprise)
        self.assertEqual(error.exception.detail, 'Facture déjà payée')

    def test_currency_minor_units(self):
        self.assertEqual(minor_amount('120', 'JPY'), 120)
        self.assertEqual(minor_amount('12.34', 'MAD'), 1234)
        self.assertEqual(minor_amount('1.23', 'KWD'), 1230)
        with self.assertRaises(HTTPException):
            minor_amount('1.23', 'JPY')

    def test_dashboard_uses_current_enterprise_key(self):
        with patch('stripe.Balance.retrieve', return_value=NS(available=[NS(amount=1234, currency='mad')])) as balance, patch('stripe.PaymentIntent.list', return_value=NS(data=[])) as payments:
            result = stripe_dashboard(self.ctx)['data']
        self.assertEqual(result['available'], [{'amount': 12.34, 'currency': 'MAD'}])
        balance.assert_called_once_with(api_key='sk_test_private')
        payments.assert_called_once_with(api_key='sk_test_private', limit=10)

    def test_checkout_filters_tenant_and_invoice_type(self):
        self.db.query.return_value.filter.return_value.first.return_value = None
        with self.assertRaises(HTTPException) as error:
            invoice_checkout(uuid4(), self.db, self.ctx)
        self.assertEqual(error.exception.status_code, 404)
        filters = ' '.join(str(item) for item in self.db.query.return_value.filter.call_args.args)
        self.assertIn('documents.enterprise_id', filters)
        self.assertIn('documents.type', filters)
        self.assertIn('documents.is_deleted', filters)

    def prepare_email(self):
        self.db.query.return_value.filter.return_value.first.side_effect = [self.doc, NS(email='client@example.com')]
        self.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    def test_global_key_does_not_enable_unconnected_enterprise(self):
        self.prepare_email()
        self.enterprise.resend_api_key = None
        with patch.object(settings, 'RESEND_API_KEY', 're_global'), patch('app.api.v1.documents.send_email') as send:
            with self.assertRaises(HTTPException) as error:
                asyncio.run(send_document(self.doc.id, 'invoice', self.db, self.ctx))
        self.assertEqual(error.exception.status_code, 400)
        self.assertIn('Resend non connecté', error.exception.detail)
        send.assert_not_called()
        self.db.commit.assert_not_called()

    def test_send_pdf_and_update_only_after_success(self):
        self.prepare_email()
        with patch.object(settings, 'RESEND_API_KEY', 're_test'), patch.object(settings, 'RESEND_FROM_EMAIL', 'billing@example.com'), patch('app.api.v1.documents.generate_pdf', return_value=b'%PDF-test'), patch('app.api.v1.documents.send_email', return_value={'id': 'email-1'}) as send:
            result = asyncio.run(send_document(self.doc.id, 'invoice', self.db, self.ctx))
        self.assertEqual(send.call_args.args[0], 're_tenant')
        payload = send.call_args.args[1]
        self.assertEqual(payload['to'], ['client@example.com'])
        self.assertEqual(base64.b64decode(payload['attachments'][0]['content']), b'%PDF-test')
        self.assertIn('24.68 MAD', payload['text'])
        self.assertEqual(result['data'].status, 'sent')
        self.assertIsNotNone(self.doc.sent_at.tzinfo)
        self.db.commit.assert_called_once()

    def test_failed_send_does_not_update_document(self):
        self.prepare_email()
        with patch.object(settings, 'RESEND_API_KEY', 're_test'), patch.object(settings, 'RESEND_FROM_EMAIL', 'billing@example.com'), patch('app.api.v1.documents.generate_pdf', return_value=b'%PDF-test'), patch('app.api.v1.documents.send_email', side_effect=RuntimeError('private re_test')):
            with self.assertRaises(HTTPException) as error:
                asyncio.run(send_document(self.doc.id, 'quote', self.db, self.ctx))
        self.assertEqual(error.exception.status_code, 502)
        self.assertNotIn('re_test', error.exception.detail)
        self.assertEqual(self.doc.status, 'draft')
        self.assertIsNone(self.doc.sent_at)
        self.db.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
