import { DocumentListPage, DocumentDetailPage } from '../invoices/DocumentPages'
import { DocumentCreatePage } from '../invoices/DocumentCreatePage'

export function QuoteListPage() { return <DocumentListPage kind="quotes" /> }
export function QuoteDetailPage() { return <DocumentDetailPage kind="quotes" /> }
export function QuoteCreatePage() { return <DocumentCreatePage kind="quotes" /> }
