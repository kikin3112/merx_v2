import { useState } from 'react';
import { TUTORIALES } from '../../data/tutorial-content';

const CONCEPTOS_RELEVANTES = [
  'costoIngredientes',
  'costoManoObra',
  'costosIndirectos',
  'margenContribucion',
  'puntoEquilibrio',
  'margenSeguridad',
  'analisisSensibilidad',
  'margenObjetivo',
  'precioSugerido',
] as const;

export function HelpPanel() {
  const [open, setOpen] = useState(false);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
        className="fixed bottom-20 right-4 z-40 bg-amber-500 hover:bg-amber-600 text-white rounded-full px-4 py-2 shadow-lg text-sm font-medium flex items-center gap-2 transition-colors"
      >
        🕯️ ¿Cómo funciona esto?
      </button>

      {open && (
        <div className="fixed inset-0 z-50 flex">
          <div className="flex-1 bg-black/30" onClick={() => setOpen(false)} />
          <div className="w-80 bg-white shadow-2xl overflow-y-auto flex flex-col">
            <div className="bg-amber-500 text-white p-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-2xl">🕯️</span>
                <div>
                  <p className="font-bold">Tu Socia explica</p>
                  <p className="text-xs text-amber-100">Cada concepto en palabras simples</p>
                </div>
              </div>
              <button onClick={() => setOpen(false)} className="text-white hover:text-amber-100 text-xl">×</button>
            </div>
            <div className="flex-1 p-4 space-y-4">
              {CONCEPTOS_RELEVANTES.map((key) => {
                const t = TUTORIALES[key];
                return (
                  <div key={key} className="border-b border-gray-100 pb-4 last:border-0">
                    <p className="font-semibold text-sm text-gray-800 mb-1">{t.titulo}</p>
                    <p className="text-xs text-gray-600 mb-2">{t.explicacion}</p>
                    <div className="bg-amber-50 rounded-lg px-3 py-2">
                      <p className="text-xs text-amber-700 italic">📌 {t.ejemplo}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
