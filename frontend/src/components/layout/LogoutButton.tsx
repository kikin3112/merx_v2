import { useClerk } from '@clerk/clerk-react';
import { ArrowRightStartOnRectangleIcon } from '@heroicons/react/24/outline';
import { useAuthStore } from '../../stores/authStore';

const CLERK_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

interface Props {
  className: string;
  onBeforeLogout?: () => void;
}

// Inner component — only rendered when ClerkProvider is active
function ClerkLogoutBtn({ className, onBeforeLogout }: Props) {
  const { signOut } = useClerk();
  const logout = useAuthStore((s) => s.logout);
  return (
    <button
      onClick={() => { onBeforeLogout?.(); logout(); signOut(); }}
      className={className}
      title="Cerrar sesión"
    >
      <ArrowRightStartOnRectangleIcon className="h-4 w-4" />
    </button>
  );
}

function LegacyLogoutBtn({ className, onBeforeLogout }: Props) {
  const logout = useAuthStore((s) => s.logout);
  return (
    <button
      onClick={() => { onBeforeLogout?.(); logout(); }}
      className={className}
      title="Cerrar sesión"
    >
      <ArrowRightStartOnRectangleIcon className="h-4 w-4" />
    </button>
  );
}

export default function LogoutButton(props: Props) {
  if (CLERK_KEY) return <ClerkLogoutBtn {...props} />;
  return <LegacyLogoutBtn {...props} />;
}
