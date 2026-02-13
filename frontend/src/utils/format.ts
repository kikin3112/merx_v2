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

export function statusColor(estado: string): string {
  const colors: Record<string, string> = {
    PENDIENTE: 'bg-yellow-100 text-yellow-800',
    CONFIRMADA: 'bg-blue-100 text-blue-800',
    FACTURADA: 'bg-green-100 text-green-800',
    ANULADA: 'bg-red-100 text-red-800',
    PAGADA: 'bg-green-100 text-green-800',
    PARCIAL: 'bg-orange-100 text-orange-800',
    EMITIDA: 'bg-blue-100 text-blue-800',
    VIGENTE: 'bg-blue-100 text-blue-800',
    ACEPTADA: 'bg-green-100 text-green-800',
    RECHAZADA: 'bg-red-100 text-red-800',
    VENCIDA: 'bg-orange-100 text-orange-800',
    ACTIVO: 'bg-green-100 text-green-800',
  };
  return colors[estado] || 'bg-gray-100 text-gray-800';
}
