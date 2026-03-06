import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import BottomNav from './BottomNav';
import MobileDrawer from './MobileDrawer';
import WhatsAppButton from '../ui/WhatsAppButton';

export default function AppShell() {
  const [drawerOpen, setDrawerOpen] = useState(false);

  return (
    <div className="flex h-screen overflow-hidden cv-bg">
      <Sidebar />
      <main className="flex-1 overflow-y-auto pb-24 lg:pb-0" style={{ backgroundColor: 'var(--cv-bg)', position: 'relative', zIndex: 1 }}>
        <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8 lg:py-6">
          <Outlet />
        </div>
      </main>
      <BottomNav onMenuOpen={() => setDrawerOpen(true)} />
      <MobileDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
      <WhatsAppButton />
    </div>
  );
}
