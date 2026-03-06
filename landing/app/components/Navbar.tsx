'use client';

import { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';

const APP_URL = process.env.NEXT_PUBLIC_APP_URL || 'https://app.chandelierp.com';

const navLinks = [
  { label: 'Funciones', href: '/#funciones' },
  { label: 'Precios', href: '/#precios' },
  { label: 'Blog', href: '/blog' },
];

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <nav
      className="sticky top-0 z-50 backdrop-blur-md border-b"
      style={{
        background: 'rgba(58,58,58,0.92)',
        borderColor: 'rgba(255,255,255,0.08)',
      }}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center">
            <Image
              src="/logo-grande.png"
              alt="chandelierp"
              width={140}
              height={40}
              className="h-8 w-auto object-contain"
              priority
            />
          </Link>

          {/* Desktop links */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className="text-sm font-medium transition-colors"
                style={{ color: 'var(--text-muted)' }}
                onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--text)')}
                onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
              >
                {link.label}
              </Link>
            ))}
            <a
              href={`${APP_URL}/registro`}
              className="inline-flex items-center px-5 py-2 rounded-lg text-sm font-semibold transition-all"
              style={{
                background: 'var(--primary)',
                color: '#1A1A1A',
              }}
            >
              Probar Gratis
            </a>
          </div>

          {/* Mobile hamburger */}
          <button
            type="button"
            className="md:hidden p-2 rounded-md transition-colors"
            style={{ color: 'var(--text-muted)' }}
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label={mobileOpen ? 'Cerrar menú' : 'Abrir menú'}
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              {mobileOpen
                ? <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />}
            </svg>
          </button>
        </div>

        {/* Mobile menu */}
        {mobileOpen && (
          <div
            className="md:hidden pb-4 border-t"
            style={{ borderColor: 'rgba(255,255,255,0.08)' }}
          >
            <div className="flex flex-col gap-1 pt-4">
              {navLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="px-3 py-2.5 rounded-lg text-sm font-medium"
                  style={{ color: 'var(--text-muted)' }}
                  onClick={() => setMobileOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <a
                href={`${APP_URL}/registro`}
                className="mx-0 mt-3 inline-flex items-center justify-center px-5 py-2.5 rounded-lg text-sm font-semibold transition-all"
                style={{ background: 'var(--primary)', color: '#1A1A1A' }}
              >
                Probar Gratis
              </a>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
