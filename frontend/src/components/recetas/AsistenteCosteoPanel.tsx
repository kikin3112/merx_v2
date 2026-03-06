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
    setUserInput('');
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
          <div className="w-10 h-10 border-4 border-t-transparent rounded-full animate-spin" style={{ borderColor: 'var(--cv-primary)', borderTopColor: 'transparent' }} />
          <p className="text-sm cv-muted">Socia esta analizando tu receta...</p>
        </div>
      )}

      {/* Error */}
      {fase === 'error' && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
          <p className="text-2xl">Hmm...</p>
          <p className="text-sm cv-muted">{errorMsg}</p>
          <button
            onClick={() => { setFase('cargando'); fase1Mutation.mutate(); }}
            className="cv-btn cv-btn-primary"
          >
            Intentar de nuevo
          </button>
        </div>
      )}

      {/* Fase 1: Analisis estructurado */}
      {fase === 'analisis' && analisis && (
        <div className="flex-1 overflow-y-auto p-4 md:p-5 space-y-4">
          {/* Precio sugerido — destacado */}
          <div className="cv-card p-4" style={{ background: 'var(--cv-primary-dim)', borderColor: 'var(--cv-primary)' }}>
            <p className="cv-section-label mb-1">Precio sugerido por Socia</p>
            <p className="text-2xl font-bold cv-text">
              {formatCurrency(Number(analisis.precio_sugerido))}
            </p>
            <p className="text-sm cv-muted mt-1">
              Margen esperado: <strong style={{ color: 'var(--cv-primary)' }}>{Number(analisis.margen_esperado).toFixed(1)}%</strong>
            </p>
          </div>

          {/* Escenario recomendado */}
          <div className="cv-card p-3 cv-alert-positive">
            <p className="cv-section-label mb-1">Escenario recomendado</p>
            <p className="text-sm font-semibold cv-text">{analisis.escenario_recomendado}</p>
          </div>

          {/* Justificacion */}
          <div>
            <p className="cv-section-label mb-1">Lo que te dice Socia</p>
            <p className="text-sm cv-text leading-relaxed">{analisis.justificacion}</p>
          </div>

          {/* Alertas */}
          {analisis.alertas.length > 0 && (
            <div className="space-y-1.5">
              <p className="cv-section-label">Ojo con esto</p>
              {analisis.alertas.map((alerta, i) => (
                <div key={i} className="cv-alert-accent flex items-start gap-2 px-3 py-2">
                  <span className="mt-0.5 flex-shrink-0" style={{ color: 'var(--cv-accent)' }}>!</span>
                  <p className="text-sm cv-text">{alerta}</p>
                </div>
              ))}
            </div>
          )}

          {/* Mensaje cierre */}
          <div className="cv-card p-3">
            <p className="text-sm cv-text italic">"{analisis.mensaje_cierre}"</p>
            <p className="text-xs cv-muted mt-1 text-right">- Socia</p>
          </div>

          {/* Pregunta de continuacion */}
          <div className="border-t border-[var(--cv-divider)] pt-4">
            <p className="text-sm font-medium cv-text text-center mb-3">
              Tienes mas preguntas para Socia?
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setFase('chat')}
                className="cv-btn cv-btn-primary flex-1"
              >
                Si, preguntarle
              </button>
              <button
                onClick={onClose}
                className="cv-btn cv-btn-ghost flex-1"
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
              <div className="cv-card px-3 py-2 text-xs cv-muted" style={{ background: 'var(--cv-primary-dim)', borderColor: 'var(--cv-primary)' }}>
                Precio sugerido: <strong style={{ color: 'var(--cv-primary)' }}>{formatCurrency(Number(analisis.precio_sugerido))}</strong>
                {' · '}Margen: <strong style={{ color: 'var(--cv-primary)' }}>{Number(analisis.margen_esperado).toFixed(1)}%</strong>
              </div>
            )}

            {/* Mensaje inicial de Socia en el chat */}
            {chatHistory.length === 0 && (
              <div className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0" style={{ background: 'var(--cv-primary)' }}>S</div>
                <div className="rounded-2xl rounded-tl-none px-3 py-2 max-w-xs" style={{ background: 'var(--cv-surface)' }}>
                  <p className="text-sm cv-text">Claro que si, hagamosle! Que mas quieres saber sobre el precio de tu receta?</p>
                </div>
              </div>
            )}

            {/* Historial de mensajes */}
            {chatHistory.map((msg, i) => (
              <div key={i} className={`flex items-start gap-2 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0" style={{ background: 'var(--cv-primary)' }}>S</div>
                )}
                <div
                  className={`rounded-2xl px-3 py-2 max-w-xs text-sm ${msg.role === 'user' ? 'rounded-tr-none ml-auto text-white' : 'rounded-tl-none cv-text'}`}
                  style={msg.role === 'user' ? { background: 'var(--cv-primary)' } : { background: 'var(--cv-surface)' }}
                >
                  {msg.content}
                </div>
              </div>
            ))}

            {/* Indicador de escritura */}
            {fase2Mutation.isPending && (
              <div className="flex items-start gap-2">
                <div className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs flex-shrink-0" style={{ background: 'var(--cv-primary)' }}>S</div>
                <div className="rounded-2xl rounded-tl-none px-3 py-2" style={{ background: 'var(--cv-surface)' }}>
                  <span className="cv-muted text-sm">Socia esta escribiendo...</span>
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Input de chat */}
          <div className="border-t border-[var(--cv-divider)] p-3 flex gap-2">
            <textarea
              value={userInput}
              onChange={(e) => setUserInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Escribele a Socia..."
              rows={1}
              className="cv-input flex-1 resize-none"
            />
            <button
              onClick={handleEnviarMensaje}
              disabled={!userInput.trim() || fase2Mutation.isPending}
              className="cv-btn cv-btn-primary"
            >
              Enviar
            </button>
          </div>
        </>
      )}
    </div>
  );
}
