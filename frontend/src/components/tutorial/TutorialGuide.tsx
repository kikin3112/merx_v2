import { useEffect, useRef } from 'react';

interface PasoTour {
  titulo: string;
  descripcion: string;
  elementoId?: string;
}

const PASOS: PasoTour[] = [
  {
    titulo: 'Crea tu primera receta',
    descripcion: 'Aquí registras cómo haces cada producto: los ingredientes, cuánto tiempo tardas y cuánto te cuesta tu trabajo.',
    elementoId: 'btn-nueva-receta',
  },
  {
    titulo: 'No olvides tus gastos del negocio',
    descripcion: 'El gas, los empaques, la electricidad... también hacen parte del costo de tu producto. Agrégalos en la pestaña "Gastos adicionales".',
    elementoId: 'tab-indirectos',
  },
  {
    titulo: 'Calcula cuánto te cuesta cada producto',
    descripcion: 'Haz clic en "Calcular costo" en cualquier receta. Te mostramos el desglose completo: materiales, tu trabajo y los gastos adicionales.',
  },
  {
    titulo: '¿Cuántas unidades necesitas vender?',
    descripcion: 'En la pestaña "Análisis de precios" puedes calcular tu punto de equilibrio. Dinos tus gastos fijos del mes y cuántas unidades esperas vender.',
    elementoId: 'tab-analisis',
  },
  {
    titulo: 'Explora diferentes precios',
    descripcion: 'También puedes ver qué pasaría con tus ganancias si cobras más o menos. Compara 5 escenarios con un solo clic.',
  },
];

interface Props {
  paso: number;
  onAvanzar: () => void;
  onOmitir: () => void;
  onCompletar: () => void;
}

export function TutorialGuide({ paso, onAvanzar, onOmitir, onCompletar }: Props) {
  const ref = useRef<HTMLDivElement>(null);
  const pasoActual = PASOS[paso];
  const esUltimo = paso === PASOS.length - 1;

  // Resaltar elemento objetivo
  useEffect(() => {
    if (!pasoActual?.elementoId) return;
    const el = document.getElementById(pasoActual.elementoId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      el.classList.add('ring-2', 'ring-amber-400', 'ring-offset-2');
      return () => el.classList.remove('ring-2', 'ring-amber-400', 'ring-offset-2');
    }
  }, [paso, pasoActual?.elementoId]);

  if (!pasoActual) return null;

  return (
    <div className="fixed inset-0 z-50 pointer-events-none">
      {/* Overlay suave */}
      <div className="absolute inset-0 bg-black/20 pointer-events-auto" onClick={onOmitir} />

      {/* Panel del tour */}
      <div
        ref={ref}
        className="absolute bottom-24 left-1/2 -translate-x-1/2 w-[min(380px,calc(100vw-2rem))] bg-white rounded-2xl shadow-2xl border border-amber-200 pointer-events-auto"
      >
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-amber-400 rounded-t-2xl px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🕯️</span>
            <span className="text-white font-bold text-sm">Tu Socia te guía</span>
          </div>
          <button onClick={onOmitir} className="text-amber-100 hover:text-white text-lg leading-none">×</button>
        </div>

        {/* Progreso */}
        <div className="px-4 pt-3">
          <div className="flex gap-1.5">
            {PASOS.map((_, i) => (
              <div
                key={i}
                className={`h-1.5 flex-1 rounded-full transition-colors ${
                  i <= paso ? 'bg-amber-400' : 'bg-gray-200'
                }`}
              />
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-1">Paso {paso + 1} de {PASOS.length}</p>
        </div>

        {/* Contenido */}
        <div className="px-4 py-3">
          <p className="font-bold text-gray-900 text-sm mb-2">{pasoActual.titulo}</p>
          <p className="text-sm text-gray-600 leading-relaxed">{pasoActual.descripcion}</p>
        </div>

        {/* Acciones */}
        <div className="px-4 pb-4 flex gap-2">
          <button
            onClick={onOmitir}
            className="flex-1 py-2 text-sm text-gray-500 hover:bg-gray-50 rounded-lg transition-colors"
          >
            Omitir tour
          </button>
          <button
            onClick={esUltimo ? onCompletar : onAvanzar}
            className="flex-1 py-2 text-sm font-semibold bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
          >
            {esUltimo ? '¡Listo! 🎉' : 'Siguiente →'}
          </button>
        </div>
      </div>
    </div>
  );
}
