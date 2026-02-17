import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

// Extend Window interface for gtag
declare global {
  interface Window {
    gtag?: (...args: unknown[]) => void;
  }
}

/**
 * Hook para trackear pageviews en navegación SPA
 * Debe usarse dentro de un componente envuelto por BrowserRouter
 */
export function usePageTracking() {
  const location = useLocation();

  useEffect(() => {
    // Skip if gtag is not available (blocked by adblocker or not loaded)
    if (typeof window.gtag !== 'function') return;

    // Track pageview with current path
    window.gtag('event', 'page_view', {
      page_path: location.pathname + location.search,
      page_title: document.title,
    });
  }, [location.pathname, location.search]);
}

/**
 * Track custom events
 * @example trackEvent('button_click', { button_name: 'create_invoice' })
 */
export function trackEvent(eventName: string, params?: Record<string, unknown>) {
  if (typeof window.gtag !== 'function') return;

  window.gtag('event', eventName, params);
}

/**
 * Track user login
 */
export function trackLogin(method: string = 'email') {
  trackEvent('login', { method });
}

/**
 * Track tenant selection
 */
export function trackTenantSelect(tenantName: string) {
  trackEvent('tenant_select', { tenant_name: tenantName });
}

/**
 * Track invoice creation
 */
export function trackInvoiceCreated(total: number) {
  trackEvent('invoice_created', { 
    value: total,
    currency: 'COP',
  });
}

/**
 * Track POS sale
 */
export function trackPOSSale(total: number, itemCount: number) {
  trackEvent('pos_sale', {
    value: total,
    currency: 'COP',
    item_count: itemCount,
  });
}
