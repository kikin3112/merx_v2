import { useState, useEffect } from 'react';

/**
 * Reactive hook that listens to a CSS media query via window.matchMedia.
 * Re-renders when the match state changes (e.g. window resize crossing breakpoint).
 */
export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => {
    if (typeof window === 'undefined') return false;
    return window.matchMedia(query).matches;
  });

  useEffect(() => {
    const mql = window.matchMedia(query);
    setMatches(mql.matches);

    const handler = (e: MediaQueryListEvent) => setMatches(e.matches);
    mql.addEventListener('change', handler);
    return () => mql.removeEventListener('change', handler);
  }, [query]);

  return matches;
}

/**
 * Returns breakpoint flags aligned to Tailwind defaults:
 * - isMobile:  < 768px  (below md)
 * - isTablet:  768–1023px (md but below lg)
 * - isDesktop: >= 1024px (lg+)
 */
export function useBreakpoint() {
  const isMobile = useMediaQuery('(max-width: 767px)');
  const isDesktop = useMediaQuery('(min-width: 1024px)');
  const isTablet = !isMobile && !isDesktop;

  return { isMobile, isTablet, isDesktop };
}
