export const SOCIA_THEME = {
  primary: '#F59E0B',
  primaryLight: '#FEF3C7',
  accent: '#8B5CF6',
  accentLight: '#EDE9FE',
  success: '#10B981',
  warning: '#F97316',
  danger: '#EF4444',
  background: '#FFFBF0',
};

export function getViabilidadColor(viabilidad: 'VIABLE' | 'CRITICO' | 'NO_VIABLE'): string {
  switch (viabilidad) {
    case 'VIABLE': return 'text-green-700 bg-green-100';
    case 'CRITICO': return 'text-yellow-700 bg-yellow-100';
    case 'NO_VIABLE': return 'text-red-700 bg-red-100';
  }
}

export function getMargenColor(margen: number): string {
  if (margen >= 50) return 'text-green-700 bg-green-100';
  if (margen >= 30) return 'text-yellow-700 bg-yellow-100';
  return 'text-red-700 bg-red-100';
}
