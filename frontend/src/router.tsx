import { createBrowserRouter, Navigate } from 'react-router-dom'
import { AppLayout } from './layout/AppLayout'
import { LoginPage } from './pages/auth/LoginPage'
import { RegisterPage } from './pages/auth/RegisterPage'
import { Placeholder } from './pages/Placeholder'
import { ProtectedRoute } from './ProtectedRoute'
import { InvoiceListPage, InvoiceDetailPage, InvoiceCreatePage } from './pages/invoices/InvoicePages'
import { QuoteListPage, QuoteDetailPage, QuoteCreatePage } from './pages/quotes/QuotePages'
import { ClientListPage, ClientDetailPage, ClientCreatePage } from './pages/clients/ClientPages'
import { SupplierListPage, SupplierDetailPage, SupplierCreatePage } from './pages/suppliers/SupplierPages'
import { CataloguePage } from './pages/catalogue/CataloguePages'
import { PaymentListPage, PaymentDetailPage, PaymentCreatePage } from './pages/payments/PaymentPages'
import { CompanyPage } from './pages/settings/CompanyPage'
import { IntegrationsPage } from './pages/settings/IntegrationsPage'
import { DashboardPage } from './pages/dashboard/DashboardPage'

export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },
  {
    path: '/',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'invoices', element: <InvoiceListPage /> },
      { path: 'invoices/new', element: <InvoiceCreatePage /> },
      { path: 'invoices/:id', element: <InvoiceDetailPage /> },
      { path: 'quotes', element: <QuoteListPage /> },
      { path: 'quotes/new', element: <QuoteCreatePage /> },
      { path: 'quotes/:id', element: <QuoteDetailPage /> },
      { path: 'clients', element: <ClientListPage /> },
      { path: 'clients/new', element: <ClientCreatePage /> },
      { path: 'clients/:id', element: <ClientDetailPage /> },
      { path: 'suppliers', element: <SupplierListPage /> },
      { path: 'suppliers/new', element: <SupplierCreatePage /> },
      { path: 'suppliers/:id', element: <SupplierDetailPage /> },
      { path: 'catalogue/products', element: <CataloguePage key="products" kind="products" /> },
      { path: 'catalogue/categories', element: <CataloguePage key="categories" kind="categories" /> },
      { path: 'catalogue/units', element: <CataloguePage key="units" kind="units" /> },
      { path: 'catalogue/tax-rates', element: <CataloguePage key="tax-rates" kind="tax-rates" /> },
      { path: 'payments', element: <PaymentListPage /> },
      { path: 'payments/new', element: <PaymentCreatePage /> },
      { path: 'payments/:id', element: <PaymentDetailPage /> },
      { path: 'settings/company', element: <CompanyPage /> },
      { path: 'settings/integrations', element: <IntegrationsPage /> },
      { path: 'settings/api-keys', element: <Placeholder title="Clés API" lot="Lot E — Paramètres" /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
])
