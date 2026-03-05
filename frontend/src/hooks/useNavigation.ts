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
  QueueListIcon,
} from '@heroicons/react/24/outline';
import { useAuthStore } from '../stores/authStore';

export interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<React.SVGProps<SVGSVGElement>>;
  roles: string[];
}

export interface NavGroup {
  id: string;
  label: string | null;
  items: NavItem[];
}

// All items with their group membership
const navItems: NavItem[] = [
  { to: '/', label: 'Dashboard', icon: ChartBarIcon, roles: ['admin', 'vendedor', 'contador', 'operador'] },
  { to: '/comercial', label: 'Comercial', icon: QueueListIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/pos', label: 'POS', icon: BanknotesIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/crm', label: 'CRM', icon: BriefcaseIcon, roles: ['admin', 'vendedor', 'operador'] },
  { to: '/terceros', label: 'Terceros', icon: UserGroupIcon, roles: ['admin', 'vendedor', 'contador', 'operador'] },
  { to: '/productos', label: 'Productos', icon: CubeIcon, roles: ['admin', 'operador'] },
  { to: '/inventario', label: 'Inventario', icon: ArchiveBoxIcon, roles: ['admin', 'operador'] },
  { to: '/recetas', label: 'Recetas', icon: BeakerIcon, roles: ['admin', 'operador'] },
  { to: '/cartera', label: 'Cartera', icon: CreditCardIcon, roles: ['admin', 'contador'] },
  { to: '/contabilidad', label: 'Contabilidad', icon: CalculatorIcon, roles: ['admin', 'contador'] },
  { to: '/reportes', label: 'Reportes', icon: ChartPieIcon, roles: ['admin', 'contador'] },
  { to: '/config', label: 'Config', icon: CogIcon, roles: ['admin'] },
  { to: '/soporte', label: 'Soporte', icon: LifebuoyIcon, roles: ['admin', 'vendedor', 'contador', 'operador'] },
];

// Group structure — semantic sections of the sidebar
const NAV_GROUPS: Array<{ id: string; label: string | null; paths: string[] }> = [
  { id: 'overview', label: null, paths: ['/'] },
  { id: 'comercial', label: 'Comercial', paths: ['/comercial', '/pos', '/crm', '/terceros'] },
  { id: 'operaciones', label: 'Operaciones', paths: ['/productos', '/inventario', '/recetas'] },
  { id: 'finanzas', label: 'Finanzas', paths: ['/cartera', '/contabilidad', '/reportes'] },
  { id: 'empresa', label: 'Empresa', paths: ['/config', '/soporte'] },
];

const superadminItems: NavItem[] = [
  { to: '/tenants', label: 'Tenants', icon: BuildingOffice2Icon, roles: [] },
];

const BOTTOM_NAV_PATHS = ['/', '/comercial', '/pos', '/productos'];

export function useNavigation() {
  const { user, tenantId, impersonation, rolEnTenant } = useAuthStore();

  const isSuperadminOnly = user?.es_superadmin && !tenantId;
  const effectiveRole = impersonation ? impersonation.rolEnTenant : (rolEnTenant ?? user?.rol);

  const filterByRole = (items: NavItem[]): NavItem[] => {
    if (user?.es_superadmin && !impersonation) return [];
    return items.filter(item => effectiveRole && item.roles.includes(effectiveRole));
  };

  const allowedItems = filterByRole(navItems);

  // Build groups with only allowed items
  const navGroups: NavGroup[] = NAV_GROUPS.map((group) => ({
    id: group.id,
    label: group.label,
    items: group.paths
      .map((path) => allowedItems.find((item) => item.to === path))
      .filter((item): item is NavItem => !!item),
  })).filter((group) => group.items.length > 0);

  const mainItems = allowedItems;
  const superItems = user?.es_superadmin ? superadminItems : [];

  const bottomNavItems = BOTTOM_NAV_PATHS
    .map(path => allowedItems.find(item => item.to === path))
    .filter((item): item is NavItem => !!item);

  return {
    mainItems,
    navGroups,
    superadminItems: superItems,
    bottomNavItems,
    isSuperadminOnly: !!isSuperadminOnly,
    user,
    effectiveRole,
  };
}
