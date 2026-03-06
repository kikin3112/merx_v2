import { NavLink } from 'react-router-dom';
import { useNavigation } from '../../hooks/useNavigation';

interface Props {
  onMenuOpen: () => void;
}

export default function BottomNav({ onMenuOpen }: Props) {
  const { bottomNavItems } = useNavigation();

  const leftItems = bottomNavItems.slice(0, 2);
  const rightItems = bottomNavItems.slice(2, 4);

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 lg:hidden mx-4"
      style={{ marginBottom: 'max(16px, env(safe-area-inset-bottom))' }}
    >
      <div
        className="flex items-center justify-around px-4 py-2"
        style={{
          backgroundColor: 'var(--cv-surface)',
          border: '1px solid var(--cv-border)',
          borderRadius: '24px',
        }}
      >
        {leftItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className="flex flex-col items-center gap-[3px] px-3 py-2.5 rounded-[10px] transition-colors"
            style={({ isActive }) => ({ color: isActive ? 'var(--cv-primary)' : 'var(--cv-muted)' })}
          >
            <item.icon className="h-5 w-5" />
            <span className="text-[10px] font-medium font-mono leading-tight">{item.label}</span>
          </NavLink>
        ))}

        {/* FAB central */}
        <button
          onClick={onMenuOpen}
          className="flex items-center justify-center transition-transform hover:scale-105 active:scale-95"
          style={{
            width: 48,
            height: 48,
            backgroundColor: 'var(--cv-primary)',
            borderRadius: 14,
            boxShadow: '0 4px 16px rgba(255,155,101,0.4)',
            color: '#1A1A1A',
            fontSize: 22,
            fontWeight: 700,
            flexShrink: 0,
          }}
        >
          +
        </button>

        {rightItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className="flex flex-col items-center gap-[3px] px-3 py-2.5 rounded-[10px] transition-colors"
            style={({ isActive }) => ({ color: isActive ? 'var(--cv-primary)' : 'var(--cv-muted)' })}
          >
            <item.icon className="h-5 w-5" />
            <span className="text-[10px] font-medium font-mono leading-tight">{item.label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
