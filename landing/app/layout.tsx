import type { Metadata } from 'next';
import { Plus_Jakarta_Sans } from 'next/font/google';
import './globals.css';

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['400', '600', '700'],
  variable: '--font-pjs',
});

export const metadata: Metadata = {
  title: 'chandelierp — ERP para Candelería',
  description: 'Sistema ERP completo para PyMEs de candelería. Inventario, POS, Facturación, Contabilidad y CRM. Prueba gratis 14 días.',
  keywords: ['ERP', 'candelería', 'inventario', 'POS', 'facturación', 'PyME', 'Colombia'],
  icons: { icon: '/logo.png' },
  openGraph: {
    title: 'chandelierp — ERP para Candelería',
    description: 'Sistema ERP completo para PyMEs de candelería. Prueba gratis 14 días.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${plusJakartaSans.variable}`}>
      <body className="antialiased bg-white text-gray-900 font-[var(--font-pjs)]">
        {children}
      </body>
    </html>
  );
}
