export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency',
    currency: 'COP',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatNumber(value: number, decimals = 0): string {
  return new Intl.NumberFormat('es-CO', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatDate(date: string): string {
  return new Intl.DateTimeFormat('es-CO', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  }).format(new Date(date));
}

export function formatDateTime(isoString: string): string {
  return new Intl.DateTimeFormat('es-CO', {
    dateStyle: 'short',
    timeStyle: 'short',
    timeZone: 'America/Bogota'
  }).format(new Date(isoString));
}

export function statusColor(estado: string): string {
  const colors: Record<string, string> = {
    PENDIENTE: 'cv-badge-primary',
    CONFIRMADA: 'cv-badge-accent',
    FACTURADA: 'cv-badge-positive',
    ANULADA: 'cv-badge-negative',
    PAGADA: 'cv-badge-positive',
    PARCIAL: 'cv-badge-primary',
    EMITIDA: 'cv-badge-accent',
    VIGENTE: 'cv-badge-accent',
    ACEPTADA: 'cv-badge-positive',
    RECHAZADA: 'cv-badge-negative',
    VENCIDA: 'cv-badge-primary',
    ACTIVO: 'cv-badge-positive',
  };
  return colors[estado] || 'cv-badge-neutral';
}
