/**
 * AsistenteCosteoPanel — Modal de Socia, la asistente de costeo con IA.
 *
 * Fase 1: Analisis estructurado (precio sugerido, margen, escenario, alertas).
 * Fase 2: Chat conversacional (opcional, solo si el usuario lo solicita).
 * El historial de chat NO se persiste — se destruye al cerrar el modal.
 */
import { useState, useEffect, useRef } from 'react';
import { useMutation } from '@tanstack/react-query';
import { recetas } from '../../api/endpoints';
import { formatCurrency } from '../../utils/format';
import type { SociaAnalisisResponse, ChatMessage } from '../../types';

interface Props {
  recetaId: string;
  onClose: () => void;
}

type Fase = 'cargando' | 'analisis' | 'chat' | 'error';

export function AsistenteCosteoPanel({ recetaId, onClose }: Props) {
  const [fase, setFase] = useState<Fase>('cargando');
  const [analisis, setAnalisis] = useState<SociaAnalisisResponse | null>(null);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [userInput, setUserInput] = useState('');
  const [errorMsg, setErrorMsg] = useState('');
  const chatEndRef = useRef<HTMLDivElement>(null);

  // Fase 1: Dispara automaticamente al montar — no espera accion del usuario
  const fase1Mutation = useMutation({
    mutationFn: () => recetas.consultarSocia(recetaId, { messages: [] }),
    onSuccess: ({ data }) => {
      setAnalisis(data as SociaAnalisisResponse);
      setFase('analisis');
    },
    onError: () => {
      setErrorMsg('Socia no pudo conectarse ahora. Intenta de nuevo en un momento.');
      setFase('error');
    },
  });

  // Fase 2: Chat conversacional — cada mensaje envia el historial completo
  const fase2Mutation = useMutation({
    mutationFn: (messages: ChatMessage[]) =>
      recetas.consultarSocia(recetaId, { messages }),
    onSuccess: ({ data }) => {
      const respuesta = (data as { respuesta: string }).respuesta;
      setChatHistory((prev) => [...prev, { role: 'assistant', content: respuesta }]);
      setUserInput('');
    },
    onError: () => {
      setChatHistory((prev) => [
        ...prev,
        { role: 'assistant', content: 'Ay, me perdi por un momento. Me repites la pregunta?' },
      ]);
    },
  });

  // Disparar Fase 1 al montar
  useEffect(() => {
    fase1Mutation.mutate();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [recetaId]);

  // Auto-scroll al final del chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatHistory]);

  function handleEnviarMensaje() {
    if (!userInput.trim() || fase2Mutation.isPending) return;
    const nuevoMensaje: ChatMessage = { role: 'user', content: userInput.trim() };
    const historialActualizado = [...chatHistory, nuevoMensaje];
    setChatHistory(historialActualizado);
    fase2Mutation.mutate(historialActualizado);
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleEnviarMensaje();
    }
  }

  return (
    <div className="flex flex-col flex-1 overflow-hidden">
      {/* Cargando */}
      {fase === 'cargando' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="w-10 h-10 border-4 border-amber-400 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-gray-500">Socia esta analizando tu receta...</p>
        </div>
      )}

      {/* Error */}
      {fase === 'error' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
          <p className="text-2xl">Hmm...</p>
          <p className="text-sm text-gray-600">{errorMsg}</p>
          <button
            onClick={() => { setFase('cargando'); fase1Mutation.mutate(); }}
            className="px-4 py-2 text-sm font-semibold bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* Fase 1: Analisis estructurado */}
      {fase === 'analisis' && analisis && (
        <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-4">
          {/* Precio sugerido — destacado */}
          <div className="bg-gradient-to-br from-amber-50 to-amber-100 border border-amber-200 rounded-xl p-4">
            <p className="text-xs font-medium text-amber-700 uppercase tracking-wide mb-1">Precio sugerido por Socia</p>
            <p className="text-2xl font-bold text-amber-800">
              {formatCurrency(Number(analisis.precio_sugerido))}
            </p>
            <p className="text-sm text-amber-700 mt-1">
              Margen esperado: <strong>{Number(analisis.margen_esperado).toFixed(1)}%</strong>
            </p>
          </div>

          {/* Escenario recomendado */}
          <div className="bg-green-50 border border-green-200 rounded-xl p-3">
            <p className="text-xs font-medium text-green-700 uppercase tracking-wide mb-1">Escenario recomendado</p>
            <p className="text-sm font-semibold text-green-800">{analisis.escenario_recomendado}</p>
          </div>

          {/* Justificacion */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">Lo que te dice Socia</p>
            <p className="text-sm text-gray-700 leading-relaxed">{analisis.justificacion}</p>
          </div>

          {/* Alertas */}
          {analisis.alertas.length > 0 && (
            <div className="space-y-1.5">
              <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">Ojo con esto</p>
              {analisis.alertas.map((alerta, i) => (
                <div key={i} className="flex items-start gap-2 bg-orange-50 border border-orange-200 rounded-lg px-3 py-2">
                  <span className="text-orange-500 mt-0.5 flex-shrink-0">!</span>
                  <p className="text-sm text-orange-700">{alerta}</p>
                </div>
              ))}
            </div>
          )}

          {/* Mensaje cierre */}
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-3">
            <p className="text-sm text-gray-700 italic">"{analisis.mensaje_cierre}"</p>
            <p className="text-xs text-gray-400 mt-1 text-right">- Socia</p>
          </div>

          {/* Pregunta de continuacion */}
          <div className="border-t border-gray-100 pt-4">
            <p className="text-sm font-medium text-gray-700 text-center mb-3">
              Tienes mas preguntas para Socia?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setFase('chat')}
                className="flex-1 py-2 text-sm font-semibold bg-amber-500 text-white rounded-lg hover:bg-amber-600 transition-colors"
              >
                Si, preguntarle
              </button>
              <button
                onClick={onClose}
                className="flex-1 py-2 text-sm font-medium text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
              >
                No, gracias
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Fase 2: Chat conversacional */}
      {fase === 'chat' && (
        <>
          <div className="flex-1 overflow-y-auto p-4 space-y-3">
            {/* Contexto breve del analisis inicial */}
            {analisis && (
              <div className="bg-amber-50 border border-amber-200 rounded-xl px-3 py-2 text-xs text-amber-700">
                Precio sugerido: <strong>{formatCurrency(Number(analisis.precio_sugerido))}</strong>
                {' · '}Margen: <strong>{Number(analisis.margen_esperado).toFixed(1)}%</strong>
              </div>
            )}

            {/* Mensaje inicial de Socia en el chat */}
            {chatHistory.length === 0 && (
              <div className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full bg-amber-400 flex items-center justify-center text-white text-xs flex-shrink-0">S</div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-none px-3 py-2 max-w-xs">
                  <p className="text-sm text-gray-700">Claro que si, hagamosle! Que mas quieres saber sobre el precio de tu receta?</p>
                </div>
              </div>
            )}

            {/* Historial de mensajes */}
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex items-start gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full bg-amber-400 flex items-center justify-center text-white text-xs flex-shrink-0">S</div>
                )}
                <div
                  className={`rounded-2xl px-3 py-2 max-w-xs text-sm ${
                    msg.role === 'user'
                      ? 'bg-amber-500 text-white rounded-tr-none ml-auto'
                      : 'bg-gray-100 text-gray-700 rounded-tl-none'
                  }`}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Indicador de escritura */}
            {fase2Mutation.isPending && (
              <div className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full bg-amber-400 flex items-center justify-center text-white text-xs flex-shrink-0">S</div>
                <div className="bg-gray-100 rounded-2xl rounded-tl-none px-3 py-2">
                  <span className="text-gray-400 text-sm">Socia esta escribiendo...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input de chat */}
          <div className="border-t border-gray-100 p-3 flex gap-2">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribele a Socia..."
              rows={1}
              className="flex-1 rounded-lg border border-gray-300 px-3 py-2 text-sm focus:ring-2 focus:ring-amber-400 resize-none"
            />
            <button
              onClick={handleEnviarMensaje}
              disabled={!userInput.trim() || fase2Mutation.isPending}
              className="px-3 py-2 bg-amber-500 text-white rounded-lg hover:bg-amber-600 disabled:opacity-50 transition-colors text-sm font-medium"
            >
              Enviar
            </button>
          </div>
        </>
      )}
    </div>
  );
}
