import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { ClerkProvider } from '@clerk/clerk-react';
import { esES } from '@clerk/localizations';
import './index.css';
import App from './App';

const clerkPubKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

// eslint-disable-next-line react-refresh/only-export-components
function AppRoot() {
  if (clerkPubKey) {
    return (
      <ClerkProvider publishableKey={clerkPubKey} localization={esES} afterSignOutUrl="/login">
        <App />
      </ClerkProvider>
    );
  }
  // Clerk no configurado — el login legacy sigue funcionando
  return <App />;
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppRoot />
  </StrictMode>,
);
