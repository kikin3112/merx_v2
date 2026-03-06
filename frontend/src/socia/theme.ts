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
    case 'VIABLE': return 'cv-badge-positive';
    case 'CRITICO': return 'cv-badge-accent';
    case 'NO_VIABLE': return 'cv-badge-negative';
  }
}

export function getMargenColor(margen: number): string {
  if (margen >= 50) return 'cv-badge-positive';
  if (margen >= 30) return 'cv-badge-accent';
  return 'cv-badge-negative';
}
