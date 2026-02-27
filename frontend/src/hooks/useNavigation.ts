import {
  ChartBarIcon,
  ShoppingCartIcon,
  CubeIcon,
  BeakerIcon,
  CalculatorIcon,
  CogIcon,
  DocumentTextIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
  BuildingOffice2Icon,
  BanknotesIcon,
  ChartPieIcon,
  CreditCardIcon,
  BriefcaseIcon,
  ArchiveBoxIcon,
  LifebuoyIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore } from '../stores/authStore';

export interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  roles: string[];
}

const navItems: NavItem[] = [
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
  { to: '/soporte', label: 'Soporte', icon: LifebuoyIcon, roles: ['admin', 'vendedor', 'contador', 'operador'] },
];

const superadminItems: NavItem[] = [
  { to: '/tenants', label: 'Tenants', icon: BuildingOffice2Icon, roles: [] },
];

// Bottom nav shows a curated subset (max 4 + "More" handled by the component)
const BOTTOM_NAV_PATHS = ['/', '/pos', '/ventas', '/productos'];

export function useNavigation() {
  const { user, tenantId, impersonation, rolEnTenant } = useAuthStore();

  const isSuperadminOnly = user?.es_superadmin && !tenantId;
  const effectiveRole = impersonation ? impersonation.rolEnTenant : (rolEnTenant ?? user?.rol);

  const filterByRole = (items: NavItem[]) => {
    if (user?.es_superadmin && !impersonation) return [];
    return items.filter(item => effectiveRole && item.roles.includes(effectiveRole));
  };

  const mainItems = filterByRole(navItems);
  const superItems = user?.es_superadmin ? superadminItems : [];

  // Bottom nav: subset of mainItems that are in BOTTOM_NAV_PATHS, preserving order
  const bottomNavItems = BOTTOM_NAV_PATHS
    .map(path => mainItems.find(item => item.to === path))
    .filter((item): item is NavItem => !!item);

  return {
    mainItems,
    superadminItems: superItems,
    bottomNavItems,
    isSuperadminOnly: !!isSuperadminOnly,
    user,
    effectiveRole,
  };
}
