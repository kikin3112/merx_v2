export interface PeriodValue {
  fecha_inicio: string;
  fecha_fin: string;
  label: string;
}

interface PeriodSelectorProps {
  value: PeriodValue;
  onChange: (value: PeriodValue) => void;
}

function toISO(d: Date): string {
  return d.toISOString().split('T')[0];
}

function formatLabel(inicio: string, fin: string): string {
  const fmt = (s: string) =>
    new Date(s + 'T00:00:00').toLocaleDateString('es-CO', { day: 'numeric', month: 'short' });
  return `${fmt(inicio)} – ${fmt(fin)}`;
}

// eslint-disable-next-line react-refresh/only-export-components
export function getDefaultPeriod(): PeriodValue {
  const hoy = new Date();
  const inicio = new Date(hoy);
  inicio.setDate(inicio.getDate() - 29);
  return {
    fecha_inicio: toISO(inicio),
    fecha_fin: toISO(hoy),
    label: formatLabel(toISO(inicio), toISO(hoy)),
  };
}

export default function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  function handleChange(field: 'fecha_inicio' | 'fecha_fin', v: string) {
    const next = { ...value, [field]: v };
    if (next.fecha_inicio && next.fecha_fin) {
      onChange({ ...next, label: formatLabel(next.fecha_inicio, next.fecha_fin) });
    }
  }

  return (
    <div className="flex items-center gap-2">
      <input
        type="date"
        value={value.fecha_inicio}
        max={value.fecha_fin}
        onChange={(e) => handleChange('fecha_inicio', e.target.value)}
        className="cv-input text-xs px-2 py-1.5 h-auto"
      />
      <span className="cv-muted text-xs select-none">→</span>
      <input
        type="date"
        value={value.fecha_fin}
        min={value.fecha_inicio}
        onChange={(e) => handleChange('fecha_fin', e.target.value)}
        className="cv-input text-xs px-2 py-1.5 h-auto"
      />
    </div>
  );
}
