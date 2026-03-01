import React from 'react';

interface SociaInsightProps {
  mensaje: string;
  tipo?: 'info' | 'success' | 'warning';
  className?: string;
}

const TIPO_STYLES = {
  info: 'bg-amber-50 border-amber-200 text-amber-800',
  success: 'bg-green-50 border-green-200 text-green-800',
  warning: 'bg-orange-50 border-orange-200 text-orange-800',
};

export function SociaInsight({ mensaje, tipo = 'info', className = '' }: SociaInsightProps) {
  return (
    <div className={`flex items-start gap-3 p-3 rounded-xl border ${TIPO_STYLES[tipo]} ${className}`}>
      <span className="text-xl flex-shrink-0">🕯️</span>
      <p className="text-sm font-medium leading-snug">{mensaje}</p>
    </div>
  );
}
