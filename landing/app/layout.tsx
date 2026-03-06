import type { Metadata } from 'next';
import { Inter, JetBrains_Mono } from 'next/font/google';
import './globals.css';

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  variable: '--font-inter',
  display: 'swap',
});

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500', '600'],
  variable: '--font-mono',
  display: 'swap',
});

export const metadata: Metadata = {
  title: 'chandelierp — ERP para solopreneurs',
  description: 'Control total de tu negocio. Inventario, recetas, POS, facturación y contabilidad en un solo lugar. Hecho para solopreneurs colombianos.',
  keywords: ['ERP', 'solopreneur', 'inventario', 'POS', 'facturación', 'PyME', 'Colombia'],
  icons: { icon: [{ url: '/logo-circular.svg', type: 'image/svg+xml' }, { url: '/isotipo.png', type: 'image/png' }] },
  openGraph: {
    title: 'chandelierp — ERP para solopreneurs',
    description: 'Control total de tu negocio. Prueba gratis 14 días.',
    type: 'website',
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${inter.variable} ${jetbrainsMono.variable}`}>
      <body style={{ fontFamily: 'var(--font-inter), system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  );
}
