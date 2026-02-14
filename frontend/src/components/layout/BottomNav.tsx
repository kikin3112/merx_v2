import { NavLink } from 'react-router-dom';
import { Bars3Icon } from '@heroicons/react/24/outline';
import { useNavigation } from '../../hooks/useNavigation';

interface Props {
  onMenuOpen: () => void;
}

export default function BottomNav({ onMenuOpen }: Props) {
  const { bottomNavItems } = useNavigation();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 lg:hidden pb-[env(safe-area-inset-bottom)]">
      <div className="flex items-center justify-around h-14">
        {bottomNavItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `flex flex-col items-center justify-center gap-0.5 px-2 py-1 min-w-[56px] transition-colors ${
                isActive ? 'text-primary-600' : 'text-gray-400'
              }`
            }
          >
            <item.icon className="h-5 w-5" />
            <span className="text-[10px] font-medium leading-tight">{item.label}</span>
          </NavLink>
        ))}
        <button
          onClick={onMenuOpen}
          className="flex flex-col items-center justify-center gap-0.5 px-2 py-1 min-w-[56px] text-gray-400 active:text-primary-600 transition-colors"
        >
          <Bars3Icon className="h-5 w-5" />
          <span className="text-[10px] font-medium leading-tight">Menu</span>
        </button>
      </div>
    </nav>
  );
}
