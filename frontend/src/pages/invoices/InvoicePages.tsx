import { DocumentListPage, DocumentDetailPage } from './DocumentPages'
import { DocumentCreatePage } from './DocumentCreatePage'

export function InvoiceListPage() { return <DocumentListPage kind="invoices" /> }
export function InvoiceDetailPage() { return <DocumentDetailPage kind="invoices" /> }
export function InvoiceCreatePage() { return <DocumentCreatePage kind="invoices" /> }
