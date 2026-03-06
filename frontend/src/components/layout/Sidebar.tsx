import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { StarIcon, SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../../stores/authStore';
import { useThemeStore } from '../../stores/themeStore';
import { useNavigation } from '../../hooks/useNavigation';
import CalificacionModal from '../CalificacionModal';
import LogoutButton from './LogoutButton';

const _API_ORIGIN = (import.meta.env.VITE_API_URL as string || '/api/v1').replace(/\/api\/v\d+\/?$/, '');

function buildLogoUrl(urlLogo: string | null | undefined): string {
  if (!urlLogo) return '/logo.png';
  if (urlLogo.startsWith('http') || urlLogo.startsWith('data:')) return urlLogo;
  return `${_API_ORIGIN}${urlLogo}`;
}

export default function Sidebar() {
  const { tenantName, tenantLogo } = useAuthStore();
  const { navGroups, superadminItems, isSuperadminOnly, user } = useNavigation();
  const { theme, toggleTheme } = useThemeStore();
  const [showCalificacion, setShowCalificacion] = useState(false);

  const logoSrc = buildLogoUrl(tenantLogo);
  const logoAlt = tenantName || 'chandelierp';

  return (
    <>
    <aside
      className="hidden lg:flex h-screen w-60 flex-col border-r"
      style={{ backgroundColor: 'var(--cv-surface)', borderColor: 'var(--cv-border)', position: 'relative', zIndex: 1 }}
    >
      {/* Brand */}
      <div className="relative flex items-center justify-center py-5 border-b" style={{ borderColor: 'var(--cv-border)' }}>
        <a href="https://chandelierp-landing.vercel.app/" target="_blank" rel="noopener noreferrer">
          <img
            src="/logo-grande.png"
            alt="chandelierp"
            className="h-10 object-contain"
            style={{ maxWidth: '152px' }}
          />
        </a>
        <button
          onClick={toggleTheme}
          className="absolute right-3 p-1.5 cv-icon-btn"
          title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
        >
          {theme === 'dark' ? <SunIcon className="h-4 w-4" /> : <MoonIcon className="h-4 w-4" />}
        </button>
      </div>

      {/* Nav — grouped */}
      <nav className="flex-1 overflow-y-auto py-3 px-3">
        {navGroups.map((group) => (
          <div key={group.id}>
            {group.label && (
              <p
                className="px-[10px] pt-3 pb-1.5 text-[9px] font-mono tracking-[0.15em] uppercase"
                style={{ color: 'rgba(168,168,168,0.45)' }}
              >
                {group.label}
              </p>
            )}
            {group.items.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `cv-nav-item flex items-center gap-[10px] px-[10px] py-[9px] rounded-[10px] text-[13px] font-medium mb-[2px]${isActive ? ' active' : ''}`
                }
              >
                <item.icon className="h-[18px] w-[18px] shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </div>
        ))}

        {superadminItems.length > 0 && (
          <div>
            {navGroups.length > 0 && <div className="my-2 border-t" style={{ borderColor: 'var(--cv-border)' }} />}
            <p
              className="px-[10px] pt-3 pb-1.5 text-[9px] font-mono tracking-[0.15em] uppercase"
              style={{ color: 'rgba(168,168,168,0.45)' }}
            >
              SuperAdmin
            </p>
            {superadminItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `cv-nav-item flex items-center gap-[10px] px-[10px] py-[9px] rounded-[10px] text-[13px] font-medium mb-[2px]${isActive ? ' active' : ''}`
                }
              >
                <item.icon className="h-[18px] w-[18px] shrink-0" />
                {item.label}
              </NavLink>
            ))}
          </div>
        )}
      </nav>

      {/* Calificar */}
      {!isSuperadminOnly && (
        <div className="px-3 pb-1">
          <button
            onClick={() => setShowCalificacion(true)}
            className="cv-nav-item flex w-full items-center gap-[10px] px-[10px] py-[9px] rounded-[10px] text-[13px] font-medium"
          >
            <StarIcon className="h-[18px] w-[18px] shrink-0" />
            Calificar el sistema
          </button>
        </div>
      )}

      {/* User */}
      <div className="border-t px-3 py-3" style={{ borderColor: 'var(--cv-border)' }}>
        <div className="flex items-center gap-[10px] px-[10px] py-2 rounded-[10px] cursor-pointer transition-colors hover:bg-[rgba(255,255,255,0.05)]">
          <div
            className="h-8 w-8 rounded-[8px] flex items-center justify-center shrink-0 overflow-hidden"
            style={{
              backgroundColor: 'var(--cv-primary-dim)',
              border: '1px solid rgba(255,155,101,0.3)',
            }}
          >
            <img
              src={isSuperadminOnly ? '/isotipo.png' : logoSrc}
              alt={isSuperadminOnly ? 'chandelierp' : logoAlt}
              className="h-full w-full object-contain"
              onError={(e) => { (e.currentTarget as HTMLImageElement).src = '/isotipo.png'; }}
            />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[13px] font-medium truncate" style={{ color: 'var(--cv-text)' }}>{user?.nombre || 'Usuario'}</p>
            <p className="text-[11px] truncate font-mono" style={{ color: 'var(--cv-muted)' }}>{user?.rol}</p>
          </div>
          <LogoutButton className="p-1.5 cv-icon-btn" />
        </div>
      </div>
    </aside>

    {showCalificacion && (
      <CalificacionModal onClose={() => setShowCalificacion(false)} />
    )}
  </>
  );
}
