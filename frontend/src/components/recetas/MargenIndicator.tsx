import { getMargenColor } from '../../socia/theme';

interface MargenIndicatorProps {
  margen: number;
  className?: string;
}

export function MargenIndicator({ margen: margenRaw, className = '' }: MargenIndicatorProps) {
  const margen = Number(margenRaw);
  const color = getMargenColor(margen);
  const label = margen >= 50 ? '🟢 Bueno' : margen >= 30 ? '🟡 Regular' : '🔴 Bajo';

  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${color} ${className}`}>
      {label} — {margen.toFixed(1)}%
    </span>
  );
}
