import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { pqrs } from '../../api/endpoints';
import { useAuthStore } from '../../stores/authStore';
import type { TicketPQRS, EstadoTicket, PrioridadTicket } from '../../types';

const ESTADO_STYLES: Record<EstadoTicket, string> = {
  ABIERTO: 'bg-blue-100 text-blue-700',
  EN_PROCESO: 'bg-yellow-100 text-yellow-700',
  RESUELTO: 'bg-green-100 text-green-700',
  CERRADO: 'bg-gray-100 text-gray-600',
};

const PRIORIDAD_STYLES: Record<PrioridadTicket, string> = {
  BAJA: 'bg-gray-100 text-gray-600',
  MEDIA: 'bg-blue-50 text-blue-600',
  ALTA: 'bg-orange-100 text-orange-700',
  CRITICA: 'bg-red-100 text-red-700',
};

interface TicketDetailProps {
  ticket: TicketPQRS;
  onBack: () => void;
}

export default function TicketDetail({ ticket, onBack }: TicketDetailProps) {
  const queryClient = useQueryClient();
  const { user, impersonation, rolEnTenant } = useAuthStore();
  const effectiveRole = impersonation ? impersonation.rolEnTenant : (rolEnTenant ?? user?.rol);
  const isAdmin = effectiveRole === 'admin' || user?.es_superadmin;

  const [respuesta, setRespuesta] = useState('');
  const [nuevoEstado, setNuevoEstado] = useState<string>(ticket.estado);
  const [nuevaPrioridad, setNuevaPrioridad] = useState<string>(ticket.prioridad);

  const responderMutation = useMutation({
    mutationFn: (contenido: string) => pqrs.responder(ticket.id, contenido),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pqrs'] });
      setRespuesta('');
    },
  });

  const actualizarMutation = useMutation({
    mutationFn: () => pqrs.update(ticket.id, {
      estado: nuevoEstado as EstadoTicket,
      prioridad: nuevaPrioridad as PrioridadTicket,
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pqrs'] });
    },
  });

  const handleResponder = () => {
    if (!respuesta.trim()) return;
    responderMutation.mutate(respuesta.trim());
  };

  return (
    <div>
      <button
        onClick={onBack}
        className="text-sm text-primary-500 hover:text-primary-600 font-medium mb-4 flex items-center gap-1"
      >
        <span>&larr;</span> Volver a tickets
      </button>

      <div className="bg-white rounded-xl border border-gray-200 p-5 mb-4">
        <div className="flex items-start justify-between gap-3 mb-4">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{ticket.asunto}</h2>
            <p className="text-xs text-gray-400 mt-1">
              Creado el {new Date(ticket.created_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'long', year: 'numeric' })}
            </p>
          </div>
          <div className="flex gap-1.5">
            <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${ESTADO_STYLES[ticket.estado]}`}>
              {ticket.estado.replace('_', ' ')}
            </span>
            <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${PRIORIDAD_STYLES[ticket.prioridad]}`}>
              {ticket.prioridad}
            </span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap">
          {ticket.descripcion}
        </div>

        {/* Admin controls */}
        {isAdmin && (
          <div className="mt-4 pt-4 border-t border-gray-100 flex items-end gap-3">
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Estado</label>
              <select
                value={nuevoEstado}
                onChange={(e) => setNuevoEstado(e.target.value)}
                className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
              >
                <option value="ABIERTO">Abierto</option>
                <option value="EN_PROCESO">En Proceso</option>
                <option value="RESUELTO">Resuelto</option>
                <option value="CERRADO">Cerrado</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">Prioridad</label>
              <select
                value={nuevaPrioridad}
                onChange={(e) => setNuevaPrioridad(e.target.value)}
                className="rounded-lg border border-gray-300 px-2 py-1.5 text-sm"
              >
                <option value="BAJA">Baja</option>
                <option value="MEDIA">Media</option>
                <option value="ALTA">Alta</option>
                <option value="CRITICA">Crítica</option>
              </select>
            </div>
            <button
              onClick={() => actualizarMutation.mutate()}
              disabled={actualizarMutation.isPending}
              className="rounded-lg bg-gray-100 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-200 disabled:opacity-50 transition-colors"
            >
              {actualizarMutation.isPending ? 'Guardando...' : 'Actualizar'}
            </button>
          </div>
        )}
      </div>

      {/* Respuestas (chat-style) */}
      <div className="bg-white rounded-xl border border-gray-200 p-5">
        <h3 className="text-sm font-semibold text-gray-900 mb-4">Conversación</h3>

        {(!ticket.respuestas || ticket.respuestas.length === 0) && (
          <p className="text-sm text-gray-400 text-center py-4">Sin respuestas aún.</p>
        )}

        <div className="space-y-3 mb-4">
          {ticket.respuestas?.map((r, i) => (
            <div key={i} className="flex gap-3">
              <div className="h-8 w-8 rounded-full bg-primary-100 flex items-center justify-center shrink-0">
                <span className="text-xs font-semibold text-primary-700">
                  {r.autor_nombre.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-baseline gap-2">
                  <span className="text-sm font-medium text-gray-900">{r.autor_nombre}</span>
                  <span className="text-xs text-gray-400">
                    {new Date(r.fecha).toLocaleDateString('es-CO', { day: '2-digit', month: 'short' })}{' '}
                    {new Date(r.fecha).toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' })}
                  </span>
                </div>
                <p className="text-sm text-gray-700 mt-1 whitespace-pre-wrap">{r.contenido}</p>
              </div>
            </div>
          ))}
        </div>

        {/* Reply input */}
        {ticket.estado !== 'CERRADO' && (
          <div className="border-t border-gray-100 pt-4">
            <textarea
              value={respuesta}
              onChange={(e) => setRespuesta(e.target.value)}
              placeholder="Escribe tu respuesta..."
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none resize-none"
            />
            <div className="flex justify-end mt-2">
              <button
                onClick={handleResponder}
                disabled={!respuesta.trim() || responderMutation.isPending}
                className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {responderMutation.isPending ? 'Enviando...' : 'Responder'}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
