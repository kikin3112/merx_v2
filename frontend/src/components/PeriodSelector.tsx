import { useState } from 'react';

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

const presets = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
  { label: 'Trim', days: 90 },
  { label: 'Año', year: true },
] as const;

function getPresetDates(preset: typeof presets[number]): { fecha_inicio: string; fecha_fin: string } {
  const hoy = new Date();
  const fin = toISO(hoy);

  if ('year' in preset && preset.year) {
    return { fecha_inicio: `${hoy.getFullYear()}-01-01`, fecha_fin: fin };
  }
  const inicio = new Date(hoy);
  inicio.setDate(inicio.getDate() - preset.days + 1);
  return { fecha_inicio: toISO(inicio), fecha_fin: fin };
}

export function getDefaultPeriod(): PeriodValue {
  const hoy = new Date();
  const inicio = new Date(hoy);
  inicio.setDate(inicio.getDate() - 29);
  return {
    fecha_inicio: toISO(inicio),
    fecha_fin: toISO(hoy),
    label: '30d',
  };
}

export default function PeriodSelector({ value, onChange }: PeriodSelectorProps) {
  const [showCustom, setShowCustom] = useState(false);
  const [customInicio, setCustomInicio] = useState(value.fecha_inicio);
  const [customFin, setCustomFin] = useState(value.fecha_fin);

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {presets.map((preset) => (
        <button
          key={preset.label}
          onClick={() => {
            const dates = getPresetDates(preset);
            onChange({ ...dates, label: preset.label });
            setShowCustom(false);
          }}
          className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
            value.label === preset.label && !showCustom
              ? 'bg-primary-100 text-primary-700'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {preset.label}
        </button>
      ))}
      <button
        onClick={() => setShowCustom(!showCustom)}
        className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
          value.label === 'custom'
            ? 'bg-primary-100 text-primary-700'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        Rango
      </button>
      {showCustom && (
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            value={customInicio}
            onChange={(e) => setCustomInicio(e.target.value)}
            className="px-2 py-1 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          />
          <span className="text-xs text-gray-400">a</span>
          <input
            type="date"
            value={customFin}
            onChange={(e) => setCustomFin(e.target.value)}
            className="px-2 py-1 text-xs border border-gray-300 rounded-md focus:ring-1 focus:ring-primary-500 focus:border-primary-500"
          />
          <button
            onClick={() => {
              if (customInicio && customFin) {
                onChange({ fecha_inicio: customInicio, fecha_fin: customFin, label: 'custom' });
                setShowCustom(false);
              }
            }}
            className="px-2.5 py-1 rounded-md text-xs font-medium bg-primary-500 text-white hover:bg-primary-600 transition-colors"
          >
            Aplicar
          </button>
        </div>
      )}
    </div>
  );
}
