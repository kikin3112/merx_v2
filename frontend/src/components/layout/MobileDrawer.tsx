import { useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { useNavigation } from '../../hooks/useNavigation';
import { useAuthStore } from '../../stores/authStore';
import LogoutButton from './LogoutButton';

interface Props {
  open: boolean;
  onClose: () => void;
}

export default function MobileDrawer({ open, onClose }: Props) {
  const { mainItems, superadminItems, isSuperadminOnly, user } = useNavigation();
  const { tenantName } = useAuthStore();

  // Lock body scroll when open
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [open]);

  // Close on Escape
  useEffect(() => {
    if (!open) return;
    const handler = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [open, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        className={`fixed inset-0 z-50 bg-black/50 transition-opacity duration-200 lg:hidden ${
          open ? 'opacity-100' : 'opacity-0 pointer-events-none'
        }`}
        onClick={onClose}
      />

      {/* Drawer panel */}
      <aside
        className={`fixed inset-y-0 left-0 z-50 w-72 flex flex-col transition-transform duration-200 ease-out lg:hidden ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
        style={{ backgroundColor: 'var(--cv-surface)' }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b" style={{ borderColor: 'var(--cv-border)' }}>
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg flex items-center justify-center" style={{ backgroundColor: 'var(--cv-primary-dim)' }}>
              <span className="font-bold text-sm font-brand" style={{ color: 'var(--cv-primary)' }}>C</span>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-semibold truncate font-brand" style={{ color: 'var(--cv-text)' }}>Chandelier</p>
              <p className="text-xs truncate font-mono" style={{ color: 'var(--cv-muted)' }}>
                {isSuperadminOnly ? 'Panel SuperAdmin' : tenantName || 'Sin tenant'}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 cv-icon-btn">
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 overflow-y-auto py-3 px-2">
          {mainItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/'}
              onClick={onClose}
              className={({ isActive }) =>
                `cv-nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium${isActive ? ' active' : ''}`
              }
            >
              <item.icon className="h-5 w-5 shrink-0" />
              {item.label}
            </NavLink>
          ))}

          {superadminItems.length > 0 && (
            <>
              {mainItems.length > 0 && <div className="my-2 mx-3 border-t" style={{ borderColor: 'var(--cv-border)' }} />}
              <p className="px-3 py-1 text-[10px] font-semibold uppercase tracking-wider font-mono" style={{ color: 'var(--cv-muted)' }}>
                SuperAdmin
              </p>
              {superadminItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={onClose}
                  className={({ isActive }) =>
                    `cv-nav-item flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium${isActive ? ' active' : ''}`
                  }
                >
                  <item.icon className="h-5 w-5 shrink-0" />
                  {item.label}
                </NavLink>
              ))}
            </>
          )}
        </nav>

        {/* User footer */}
        <div className="border-t p-3 pb-[env(safe-area-inset-bottom)]" style={{ borderColor: 'var(--cv-border)' }}>
          <div className="flex items-center gap-2 px-2 py-1.5">
            <div className="h-8 w-8 rounded-full flex items-center justify-center" style={{ backgroundColor: 'var(--cv-elevated)' }}>
              <span className="text-xs font-semibold font-mono" style={{ color: 'var(--cv-primary)' }}>
                {user?.nombre?.charAt(0)?.toUpperCase() || 'U'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate" style={{ color: 'var(--cv-text)' }}>{user?.nombre || 'Usuario'}</p>
              <p className="text-xs truncate font-mono" style={{ color: 'var(--cv-muted)' }}>{user?.rol}</p>
            </div>
            <LogoutButton className="p-1.5 cv-icon-btn" onBeforeLogout={onClose} />
          </div>
        </div>
      </aside>
    </>
  );
}
