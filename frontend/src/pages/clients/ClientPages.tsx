import { CrmDetailPage, CrmListPage } from './CrmPages'
import { CrmFormPage } from './CrmFormPage'

export function ClientListPage() { return <CrmListPage kind="clients" /> }
export function ClientDetailPage() { return <CrmDetailPage kind="clients" /> }
export function ClientCreatePage() { return <CrmFormPage kind="clients" /> }
