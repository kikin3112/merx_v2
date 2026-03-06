import { BrowserRouter, Routes, Route, Navigate, Outlet, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './stores/authStore';
import { usePageTracking } from './hooks/useAnalytics';
import AppShell from './components/layout/AppShell';
import ImpersonationBanner from './components/ImpersonationBanner';
import RoleGuard from './components/auth/RoleGuard';
import SuperadminGuard from './components/auth/SuperadminGuard';
import LoginPage from './pages/LoginPage';
import RegistroPage from './pages/RegistroPage';
import ClerkCallbackPage from './pages/ClerkCallbackPage';
import EmpresaWizardPage from './pages/EmpresaWizardPage';
import SelectTenantPage from './pages/SelectTenantPage';
import DashboardPage from './pages/DashboardPage';
import ProductosPage from './pages/ProductosPage';
import TercerosPage from './pages/TercerosPage';
import VentasPage from './pages/VentasPage';
import ComercialPage from './pages/ComercialPage';
import InventarioPage from './pages/InventarioPage';
import RecetasPage from './pages/RecetasPage';
import { RentabilidadPage } from './pages/RentabilidadPage';
import ContabilidadPage from './pages/ContabilidadPage';
import FacturasPage from './pages/FacturasPage';
import CotizacionesPage from './pages/CotizacionesPage';
import ConfigPage from './pages/ConfigPage';
import TenantsPage from './pages/TenantsPage';
import ReportesPage from './pages/ReportesPage';
import POSPage from './pages/POSPage';
import CarteraPage from './pages/CarteraPage';
import CRMPage from './pages/CRMPage';
import SoportePage from './pages/SoportePage';
import CatalogoPage from './pages/CatalogoPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
  },
});

function RequireAuth() {
  const token = useAuthStore((s) => s.token);
  const tenantId = useAuthStore((s) => s.tenantId);
  const user = useAuthStore((s) => s.user);
  const impersonation = useAuthStore((s) => s.impersonation);
  const location = useLocation();

  if (!token) return <Navigate to="/login" replace />;
  if (!tenantId && !user?.es_superadmin) return <Navigate to="/select-tenant" replace />;
  // Superadmin sin impersonación: acceso exclusivo a /tenants
  if (user?.es_superadmin && !impersonation && !location.pathname.startsWith('/tenants')) {
    return <Navigate to="/tenants" replace />;
  }

  return <Outlet />;
}

function RequireToken() {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}

// Component to track page views in SPA
function AnalyticsTracker() {
  usePageTracking();
  return null;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AnalyticsTracker />
        <ImpersonationBanner />
        <Routes>
          <Route path="/login/*" element={<LoginPage />} />
          <Route path="/registro" element={<RegistroPage />} />
          <Route path="/clerk-callback" element={<ClerkCallbackPage />} />

          <Route element={<RequireToken />}>
            <Route path="/select-tenant" element={<SelectTenantPage />} />
            <Route path="/registro/empresa" element={<EmpresaWizardPage />} />
          </Route>

          <Route element={<RequireAuth />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<DashboardPage />} />

              {/* Pipeline Comercial Unificado */}
              <Route path="/comercial" element={<ComercialPage />} />
              <Route path="/catalogo" element={<CatalogoPage />} />

              {/* Legacy routes — kept for backward compat, redirect to /comercial */}
              <Route path="/ventas" element={<VentasPage />} />
              <Route path="/facturas" element={<FacturasPage />} />
              <Route path="/cotizaciones" element={<CotizacionesPage />} />
              <Route path="/crm" element={<CRMPage />} />
              <Route path="/terceros" element={<TercerosPage />} />
              <Route path="/pos" element={<POSPage />} />
              <Route path="/soporte" element={<SoportePage />} />

              {/* Admin + Operador only */}
              <Route path="/productos" element={
                <RoleGuard allowedRoles={['admin', 'operador']}>
                  <ProductosPage />
                </RoleGuard>
              } />
              <Route path="/inventario" element={
                <RoleGuard allowedRoles={['admin', 'operador']}>
                  <InventarioPage />
                </RoleGuard>
              } />
              <Route path="/produccion" element={
                <RoleGuard allowedRoles={['admin', 'operador']}>
                  <RecetasPage />
                </RoleGuard>
              } />
              <Route path="/produccion/rentabilidad" element={
                <RoleGuard allowedRoles={['admin', 'operador']}>
                  <RentabilidadPage />
                </RoleGuard>
              } />

              {/* Admin + Contador only */}
              <Route path="/cartera" element={
                <RoleGuard allowedRoles={['admin', 'contador']}>
                  <CarteraPage />
                </RoleGuard>
              } />
              <Route path="/contabilidad" element={
                <RoleGuard allowedRoles={['admin', 'contador']}>
                  <ContabilidadPage />
                </RoleGuard>
              } />
              <Route path="/reportes" element={
                <RoleGuard allowedRoles={['admin', 'contador']}>
                  <ReportesPage />
                </RoleGuard>
              } />

              {/* Admin only */}
              <Route path="/config" element={
                <RoleGuard allowedRoles={['admin']}>
                  <ConfigPage />
                </RoleGuard>
              } />

              {/* Superadmin only */}
              <Route path="/tenants" element={
                <SuperadminGuard>
                  <TenantsPage />
                </SuperadminGuard>
              } />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
