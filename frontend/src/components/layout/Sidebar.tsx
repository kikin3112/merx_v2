import { NavLink } from 'react-router-dom';
import { ArrowRightStartOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../../stores/authStore';
import { useNavigation } from '../../hooks/useNavigation';

const _API_ORIGIN = (import.meta.env.VITE_API_URL as string || '/api/v1').replace(/\/api\/v\d+\/?$/, '');

function buildLogoUrl(urlLogo: string | null | undefined): string {
  if (!urlLogo) return '/logo.png';
  if (urlLogo.startsWith('http')) return urlLogo;
  return `${_API_ORIGIN}${urlLogo}`;
}

export default function Sidebar() {
  const { tenantName, tenantLogo, logout } = useAuthStore();
  const { mainItems, superadminItems, isSuperadminOnly, user } = useNavigation();

  const logoSrc = buildLogoUrl(tenantLogo);
  const logoAlt = tenantName || 'ChandeliERP';

  return (
    <aside className="hidden lg:flex h-screen w-60 flex-col bg-white border-r border-gray-200">
      {/* Brand */}
      <div className="flex items-center gap-2 px-4 py-5 border-b border-gray-100">
        <img
          src={logoSrc}
          alt={logoAlt}
          className="h-8 w-8 rounded-full object-cover shrink-0"
          onError={(e) => { (e.currentTarget as HTMLImageElement).src = '/logo.png'; }}
        />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-gray-900 truncate">{tenantName || 'Chandelier'}</p>
          <p className="text-xs text-gray-500 truncate">
            {isSuperadminOnly ? 'Panel SuperAdmin' : tenantName || 'Sin tenant'}
          </p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3 px-2">
        {mainItems.map((item) => (
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

        {superadminItems.length > 0 && (
          <>
            {mainItems.length > 0 && <div className="my-2 mx-3 border-t border-gray-200" />}
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
