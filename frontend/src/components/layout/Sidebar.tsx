import { NavLink } from 'react-router-dom';
import {
  ChartBarIcon,
  ShoppingCartIcon,
  CubeIcon,
  BeakerIcon,
  CalculatorIcon,
  CogIcon,
  ArrowRightStartOnRectangleIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
  BuildingOffice2Icon,
  BanknotesIcon,
  ChartPieIcon,
  CreditCardIcon,
  BriefcaseIcon,
  ArchiveBoxIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore } from '../../stores/authStore';

const navItems = [
  { to: '/', label: 'Dashboard', icon: ChartBarIcon, roles: ['admin', 'vendedor', 'contador', 'operador'] },
  { to: '/pos', label: 'POS', icon: BanknotesIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/ventas', label: 'Ventas', icon: ShoppingCartIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/facturas', label: 'Facturas', icon: DocumentTextIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/cotizaciones', label: 'Cotizaciones', icon: ClipboardDocumentListIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/crm', label: 'CRM', icon: BriefcaseIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/productos', label: 'Productos', icon: CubeIcon, roles: ['admin', 'operador'] },
  { to: '/terceros', label: 'Terceros', icon: UserGroupIcon, roles: ['admin', 'vendedor', 'contador', 'operador'] },
  { to: '/inventario', label: 'Inventario', icon: ArchiveBoxIcon, roles: ['admin', 'operador'] },
  { to: '/recetas', label: 'Recetas', icon: BeakerIcon, roles: ['admin', 'operador'] },
  { to: '/cartera', label: 'Cartera', icon: CreditCardIcon, roles: ['admin', 'contador'] },
  { to: '/contabilidad', label: 'Contabilidad', icon: CalculatorIcon, roles: ['admin', 'contador'] },
  { to: '/reportes', label: 'Reportes', icon: ChartPieIcon, roles: ['admin', 'contador'] },
  { to: '/config', label: 'Config', icon: CogIcon, roles: ['admin'] },
];

const superadminItems = [
  { to: '/tenants', label: 'Tenants', icon: BuildingOffice2Icon },
];

export default function Sidebar() {
  const { tenantName, tenantId, user, impersonation, logout } = useAuthStore();

  const isSuperadminOnly = user?.es_superadmin && !tenantId;

  // Determine effective role (impersonation takes precedence)
  const effectiveRole = impersonation
    ? impersonation.rolEnTenant
    : user?.rol;

  return (
    <aside className="flex h-screen w-60 flex-col bg-white border-r border-gray-200">
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-gray-100">
        <div className="h-8 w-8 rounded-lg bg-primary-500 flex items-center justify-center">
          <span className="text-white font-bold text-sm">C</span>
        </div>
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">Chandelier</p>
          <p className="text-xs text-gray-500 truncate">
            {isSuperadminOnly ? 'Panel SuperAdmin' : tenantName || 'Sin tenant'}
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {/* Tenant-scoped nav: only show when a tenant is selected and user has role access */}
        {!isSuperadminOnly && navItems
          .filter(item => {
            // Superadmin (not impersonating) sees all
            if (user?.es_superadmin && !impersonation) return true;
            // Filter by role
            return effectiveRole && item.roles.includes(effectiveRole);
          })
          .map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }`
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}

        {user?.es_superadmin && (
          <>
            {!isSuperadminOnly && <div className="my-2 mx-3 border-t border-gray-200" />}
            <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider text-gray-400">
              SuperAdmin
            </p>
            {superadminItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-secondary-50 text-secondary-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`
                }
              >
                <item.icon className="h-5 w-5 shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </>
        )}
      </nav>

      {/* User */}
      <div className="border-t border-gray-100 p-3">
        <div className="flex items-center gap-2 px-2 py-1.5">
          <div className="h-8 w-8 rounded-full bg-secondary-100 flex items-center justify-center">
            <span className="text-secondary-700 text-xs font-semibold">
              {user?.nombre?.charAt(0)?.toUpperCase() || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-gray-900 truncate">{user?.nombre || 'Usuario'}</p>
            <p className="text-xs text-gray-500 truncate">{user?.rol}</p>
          </div>
          <button
            onClick={logout}
            className="p-1.5 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
            title="Cerrar sesion"
          >
            <ArrowRightStartOnRectangleIcon className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
