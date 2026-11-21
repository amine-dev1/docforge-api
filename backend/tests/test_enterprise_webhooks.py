import hashlib
import hmac
import json
import time
import unittest
from decimal import Decimal
from types import SimpleNamespace as NS
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import HTTPException

from app.api.v1.tenant import ResendConnect, connect_resend, disconnect_resend
from app.api.v1.webhooks import process_stripe_webhook
from app.models.tenant import Enterprise
from app.models.document import Document
from app.models.finance import Payment, PaymentAllocation
from app.services.resend_service import validate_resend_key, send_email


class ResendTests(unittest.TestCase):
    def test_invalid_key_preserves_connection(self):
        enterprise = NS(resend_api_key='re_original', resend_from_email='original@example.com')
        db = MagicMock()
        with patch('app.services.resend_service.requests.get', return_value=NS(status_code=401, json=lambda: {'name': 'validation_error'})):
            with self.assertRaises(HTTPException) as error:
                connect_resend(ResendConnect(api_key='re_invalid', from_email='a@example.com'), db, NS(enterprise=enterprise))
        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(enterprise.resend_api_key, 're_original')
        db.commit.assert_not_called()

    def test_full_and_sending_only_keys(self):
        for response in (NS(status_code=200), NS(status_code=403, json=lambda: {'name': 'restricted_api_key'})):
            with patch('app.services.resend_service.requests.get', return_value=response):
                validate_resend_key('re_test')

    def test_connect_disconnect(self):
        enterprise = NS()
        db = MagicMock()
        with patch('app.api.v1.tenant.validate_resend_key') as validate:
            connect_resend(ResendConnect(api_key='re_test', from_email='a@example.com'), db, NS(enterprise=enterprise))
            validate.assert_called_once_with('re_test')
        self.assertEqual(enterprise.resend_api_key, 're_test')
        disconnect_resend(db, NS(enterprise=enterprise))
        self.assertIsNone(enterprise.resend_api_key)
        self.assertIsNone(enterprise.resend_from_email)

    def test_credentials_are_per_request(self):
        with patch('app.services.resend_service.requests.post') as post:
            send_email('re_one', {'from': 'one@example.com'})
            send_email('re_two', {'from': 'two@example.com'})
        self.assertEqual([call.kwargs['headers']['Authorization'] for call in post.call_args_list],
                         ['Bearer re_one', 'Bearer re_two'])


class WebhookTests(unittest.TestCase):
    def setUp(self):
        self.enterprise_id = uuid4()
        self.doc = NS(id=uuid4(), client_id=uuid4(), currency='MAD', amount_due=Decimal('100'),
                      amount_paid=Decimal('20'), total_ttc=Decimal('120'), status='partially_paid')
        self.enterprise = NS(stripe_webhook_secret='whsec_test')
        self.queries = {model: MagicMock() for model in (Enterprise, Document, Payment)}
        for query in self.queries.values():
            query.filter.return_value = query
            query.with_for_update.return_value = query
        self.queries[Enterprise].first.return_value = self.enterprise
        self.queries[Document].first.return_value = self.doc
        self.queries[Payment].first.return_value = None
        self.db = MagicMock()
        self.db.query.side_effect = lambda model: self.queries[model]
        self.session = {'id': 'cs_test_' + 'a' * 100, 'payment_intent': 'pi_test', 'mode': 'payment',
                        'payment_status': 'paid', 'amount_total': 5000, 'currency': 'mad',
                        'metadata': {'enterprise_id': str(self.enterprise_id), 'document_id': str(self.doc.id)}}

    def deliver(self, event_type='checkout.session.completed', signature=None):
        payload = json.dumps({'type': event_type, 'data': {'object': self.session}}).encode()
        timestamp = int(time.time())
        digest = hmac.new(b'whsec_test', str(timestamp).encode() + b'.' + payload, hashlib.sha256).hexdigest()
        return process_stripe_webhook(self.enterprise_id, payload,
                                      signature if signature is not None else f't={timestamp},v1={digest}', self.db)

    def test_valid_signed_partial_payment(self):
        self.assertEqual(self.deliver(), {'received': True})
        payment, allocation = [call.args[0] for call in self.db.add.call_args_list]
        self.assertIsInstance(payment, Payment)
        self.assertIsInstance(allocation, PaymentAllocation)
        self.assertEqual(payment.amount, Decimal('50'))
        self.assertEqual(payment.status, 'confirmed')
        self.assertEqual(payment.amount_remaining, 0)
        self.assertEqual(self.doc.amount_due, Decimal('50'))
        self.assertEqual(self.doc.status, 'partially_paid')
        self.db.commit.assert_called_once()

    def test_overpayment_is_capped(self):
        self.session['amount_total'] = 15000
        self.deliver()
        self.assertEqual(self.db.add.call_args_list[0].args[0].amount, Decimal('100'))
        self.assertEqual(self.doc.amount_due, 0)
        self.assertEqual(self.doc.status, 'paid')

    def test_duplicate_does_nothing(self):
        self.queries[Payment].first.return_value = NS()
        self.deliver()
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_bad_signature(self):
        with self.assertRaises(HTTPException) as error:
            self.deliver(signature='invalid')
        self.assertEqual(error.exception.status_code, 400)
        self.db.add.assert_not_called()

    def test_missing_tenant_and_secret(self):
        for value, expected in [(None, 404), (NS(stripe_webhook_secret=None), 400)]:
            self.queries[Enterprise].first.return_value = value
            with self.assertRaises(HTTPException) as error:
                self.deliver()
            self.assertEqual(error.exception.status_code, expected)

    def test_unpaid_wrong_tenant_currency_and_invalid_metadata(self):
        original = dict(self.session)
        for changes in ({'payment_status': 'unpaid'}, {'currency': 'eur'},
                        {'metadata': {'enterprise_id': str(uuid4()), 'document_id': str(self.doc.id)}},
                        {'metadata': {'enterprise_id': str(self.enterprise_id), 'document_id': 'invalid'}}):
            self.session = original | changes
            self.deliver()
            self.db.add.assert_not_called()

    def test_missing_document(self):
        self.queries[Document].first.return_value = None
        self.deliver()
        self.db.add.assert_not_called()
        filters = ' '.join(str(arg) for arg in self.queries[Document].filter.call_args.args)
        self.assertIn('documents.enterprise_id', filters)

    def test_async_confirmation(self):
        self.deliver('checkout.session.async_payment_succeeded')
        self.db.commit.assert_called_once()

    def test_unhandled_event(self):
        self.deliver('payment_intent.created')
        self.db.add.assert_not_called()


if __name__ == '__main__':
    unittest.main()
