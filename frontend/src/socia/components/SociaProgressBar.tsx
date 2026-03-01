
import { NIVELES, getNivelInfo } from '../achievements';

interface SociaProgressBarProps {
  nivelActual: string;
  logros: string[];
}

export function SociaProgressBar({ nivelActual, logros }: SociaProgressBarProps) {
  const nivelIdx = NIVELES.findIndex((n) => n.id === nivelActual);
  const nivel = getNivelInfo(nivelActual);
  const siguiente = NIVELES[nivelIdx + 1];

  const progresoPct = siguiente
    ? Math.round(
        (siguiente.requerimientos.filter((r) => logros.includes(r)).length /
          siguiente.requerimientos.length) *
          100
      )
    : 100;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{nivel.emoji}</span>
          <div>
            <p className="text-sm font-bold text-amber-800">{nivel.nombre}</p>
            <p className="text-xs text-amber-600">{nivel.descripcion}</p>
          </div>
        </div>
        <span className="text-xs text-amber-500 font-medium">{logros.length} logros</span>
      </div>
      {siguiente && (
        <>
          <div className="w-full bg-amber-100 rounded-full h-2 mt-2">
            <div
              className="bg-amber-400 h-2 rounded-full transition-all duration-500"
              style={{ width: `${progresoPct}%` }}
            />
          </div>
          <p className="text-xs text-amber-600 mt-1">
            Siguiente nivel: {siguiente.emoji} {siguiente.nombre} — {progresoPct}% completado
          </p>
        </>
      )}
    </div>
  );
}
