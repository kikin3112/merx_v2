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

const TIPO_LABELS: Record<string, string> = {
  PETICION: 'Petición',
  QUEJA: 'Queja',
  RECLAMO: 'Reclamo',
  SUGERENCIA: 'Sugerencia',
  SOPORTE: 'Soporte',
};

interface TicketListProps {
  tickets: TicketPQRS[];
  onSelect: (ticket: TicketPQRS) => void;
}

export default function TicketList({ tickets, onSelect }: TicketListProps) {
  if (tickets.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <p className="text-lg font-medium mb-1">No hay tickets</p>
        <p className="text-sm">Crea un nuevo ticket para solicitar ayuda.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {tickets.map((ticket) => (
        <button
          key={ticket.id}
          onClick={() => onSelect(ticket)}
          className="w-full text-left bg-white rounded-lg border border-gray-200 p-4 hover:border-primary-300 hover:shadow-sm transition-all"
        >
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-gray-900 truncate">{ticket.asunto}</h3>
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ticket.descripcion}</p>
              <div className="flex items-center gap-2 mt-2 flex-wrap">
                <span className="text-xs text-gray-400">{TIPO_LABELS[ticket.tipo] || ticket.tipo}</span>
                <span className="text-gray-300">|</span>
                <span className="text-xs text-gray-400">
                  {new Date(ticket.created_at).toLocaleDateString('es-CO', { day: '2-digit', month: 'short', year: 'numeric' })}
                </span>
                {ticket.respuestas?.length > 0 && (
                  <>
                    <span className="text-gray-300">|</span>
                    <span className="text-xs text-gray-400">{ticket.respuestas.length} respuesta(s)</span>
                  </>
                )}
              </div>
            </div>
            <div className="flex flex-col items-end gap-1.5 shrink-0">
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${ESTADO_STYLES[ticket.estado]}`}>
                {ticket.estado.replace('_', ' ')}
              </span>
              <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORIDAD_STYLES[ticket.prioridad]}`}>
                {ticket.prioridad}
              </span>
            </div>
          </div>
        </button>
      ))}
    </div>
  );
}
