import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ChandeliERP — ERP para Candelería',
  description: 'Sistema ERP completo para PyMEs de candelería. Inventario, POS, Facturación, Contabilidad y CRM. Prueba gratis 14 días.',
  keywords: ['ERP', 'candelería', 'inventario', 'POS', 'facturación', 'PyME', 'Colombia'],
  openGraph: {
    title: 'ChandeliERP — ERP para Candelería',
    description: 'Sistema ERP completo para PyMEs de candelería. Prueba gratis 14 días.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body className="antialiased bg-white text-gray-900">
        {children}
      </body>
    </html>
  );
}
