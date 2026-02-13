import { BrowserRouter, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useAuthStore } from './stores/authStore';
import AppShell from './components/layout/AppShell';
import LoginPage from './pages/LoginPage';
import SelectTenantPage from './pages/SelectTenantPage';
import DashboardPage from './pages/DashboardPage';
import ProductosPage from './pages/ProductosPage';
import TercerosPage from './pages/TercerosPage';
import VentasPage from './pages/VentasPage';
import InventarioPage from './pages/InventarioPage';
import RecetasPage from './pages/RecetasPage';
import ContabilidadPage from './pages/ContabilidadPage';
import FacturasPage from './pages/FacturasPage';
import CotizacionesPage from './pages/CotizacionesPage';
import ConfigPage from './pages/ConfigPage';
import TenantsPage from './pages/TenantsPage';
import ReportesPage from './pages/ReportesPage';
import POSPage from './pages/POSPage';
import CarteraPage from './pages/CarteraPage';

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

  if (!token) return <Navigate to="/login" replace />;
  // Superadmin bypasses tenant selection — goes straight to admin panel
  if (!tenantId && !user?.es_superadmin) return <Navigate to="/select-tenant" replace />;

  return <Outlet />;
}

function SuperadminRedirect({ children }: { children: React.ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const tenantId = useAuthStore((s) => s.tenantId);
  // Superadmin without a tenant context → go to tenant management
  if (user?.es_superadmin && !tenantId) return <Navigate to="/tenants" replace />;
  return <>{children}</>;
}

function RequireToken() {
  const token = useAuthStore((s) => s.token);
  if (!token) return <Navigate to="/login" replace />;
  return <Outlet />;
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route element={<RequireToken />}>
            <Route path="/select-tenant" element={<SelectTenantPage />} />
          </Route>

          <Route element={<RequireAuth />}>
            <Route element={<AppShell />}>
              <Route path="/" element={<SuperadminRedirect><DashboardPage /></SuperadminRedirect>} />
              <Route path="/ventas" element={<VentasPage />} />
              <Route path="/facturas" element={<FacturasPage />} />
              <Route path="/cotizaciones" element={<CotizacionesPage />} />
              <Route path="/productos" element={<ProductosPage />} />
              <Route path="/terceros" element={<TercerosPage />} />
              <Route path="/inventario" element={<InventarioPage />} />
              <Route path="/recetas" element={<RecetasPage />} />
              <Route path="/cartera" element={<CarteraPage />} />
              <Route path="/contabilidad" element={<ContabilidadPage />} />
              <Route path="/reportes" element={<ReportesPage />} />
              <Route path="/pos" element={<POSPage />} />
              <Route path="/config" element={<ConfigPage />} />
              <Route path="/tenants" element={<TenantsPage />} />
            </Route>
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
