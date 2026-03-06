import { useState } from 'react';

interface Props {
  onCompletar: () => void;
}

interface MensajeSocia {
  texto: string;
  opciones?: string[];
  accion?: string;
}

const PASOS_CONVERSACION: MensajeSocia[] = [
  {
    texto: '¡Hola! Soy Socia, tu asistente de precios ✨ Estoy aquí para ayudarte a ponerle el precio justo a cada producto — velas, confites, ropa, jabones, lo que hagas — para que tu negocio crezca y nunca trabajes a pérdida.',
    opciones: ['¡Hola Socia!', 'Cuéntame más'],
  },
  {
    texto: '¿Ya tienes claro cuánto te cuesta hacer cada producto?',
    opciones: ['Más o menos', 'No tengo ni idea', 'Creo que sí'],
  },
  {
    texto: 'Perfecto. Te ayudo con eso en las recetas 💡 Ahí registras los ingredientes o insumos, tu tiempo y tus gastos. Yo hago los cálculos por ti.',
    opciones: ['¿Y los gastos del negocio?', '¿Cómo empiezo?'],
  },
  {
    texto: '¡Buena pregunta! El arriendo, los empaques, la luz... también cuentan. Los agregas en "Gastos adicionales" y yo los reparto automáticamente entre todos tus productos.',
    opciones: ['¡Eso es muy útil!', 'Entendido'],
  },
  {
    texto: '¿Lista para empezar? Crea tu primera receta y descubre cuánto te cuesta cada producto. ¡Juntas ponemos a crecer tu negocio! 🚀',
    opciones: ['¡Vamos!'],
    accion: 'completar',
  },
];

export function SociaOnboarding({ onCompletar }: Props) {
  const [paso, setPaso] = useState(0);
  const [mensajesVistos, setMensajesVistos] = useState<number[]>([0]);

  const pasoActual = PASOS_CONVERSACION[paso];

  function handleOpcion(opcion: string, accion?: string) {
    if (accion === 'completar') {
      onCompletar();
      return;
    }
    const siguientePaso = paso + 1;
    if (siguientePaso < PASOS_CONVERSACION.length) {
      setPaso(siguientePaso);
      setMensajesVistos((prev) => [...prev, siguientePaso]);
    } else {
      onCompletar();
    }
    void opcion;
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center bg-black/40">
      <div className="w-full sm:w-[420px] bg-white rounded-t-2xl sm:rounded-2xl shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-amber-500 to-violet-500 p-4 text-white">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-white/20 flex items-center justify-center text-xl">
              ✨
            </div>
            <div>
              <p className="font-bold">Socia</p>
              <p className="text-xs text-amber-100">Tu asistente de precios</p>
            </div>
          </div>
        </div>

        {/* Mensajes */}
        <div className="p-4 space-y-3 max-h-64 overflow-y-auto">
          {mensajesVistos.map((idx) => (
            <div key={idx} className="flex gap-2">
              <div className="w-7 h-7 rounded-full bg-amber-100 flex items-center justify-center flex-shrink-0 text-sm">
                ✨
              </div>
              <div className="bg-amber-50 border border-amber-100 rounded-2xl rounded-tl-none px-3 py-2 max-w-[85%]">
                <p className="text-sm text-gray-700 leading-relaxed">
                  {PASOS_CONVERSACION[idx].texto}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Opciones */}
        <div className="p-4 border-t border-gray-100 space-y-2">
          {pasoActual.opciones?.map((opcion) => (
            <button
              key={opcion}
              onClick={() => handleOpcion(opcion, pasoActual.accion)}
              className="w-full text-left px-4 py-2.5 rounded-xl border-2 border-amber-200 bg-amber-50 text-sm font-medium text-amber-800 hover:bg-amber-100 hover:border-amber-400 transition-colors"
            >
              {opcion}
            </button>
          ))}
          <button
            onClick={onCompletar}
            className="w-full text-center text-xs text-gray-400 hover:text-gray-600 py-1 transition-colors"
          >
            Omitir introducción
          </button>
        </div>
      </div>
    </div>
  );
}
