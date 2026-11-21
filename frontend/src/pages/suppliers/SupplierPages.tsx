import { CrmDetailPage, CrmListPage } from '../clients/CrmPages'
import { CrmFormPage } from '../clients/CrmFormPage'

export function SupplierListPage() { return <CrmListPage kind="suppliers" /> }
export function SupplierDetailPage() { return <CrmDetailPage kind="suppliers" /> }
export function SupplierCreatePage() { return <CrmFormPage kind="suppliers" /> }
