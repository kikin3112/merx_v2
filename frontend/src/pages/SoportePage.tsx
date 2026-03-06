import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { pqrs } from '../api/endpoints';
import type { TicketPQRS, TipoPQRS, EstadoTicket } from '../types';
import TicketList from '../components/soporte/TicketList';
import TicketDetail from '../components/soporte/TicketDetail';
import CreateTicketModal from '../components/soporte/CreateTicketModal';

export default function SoportePage() {
  const [selectedTicket, setSelectedTicket] = useState<TicketPQRS | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [filterTipo, setFilterTipo] = useState<TipoPQRS | ''>('');
  const [filterEstado, setFilterEstado] = useState<EstadoTicket | ''>('');

  const { data: tickets = [], isLoading } = useQuery<TicketPQRS[]>({
    queryKey: ['pqrs', filterTipo, filterEstado],
    queryFn: () =>
      pqrs.list({
        tipo: filterTipo || undefined,
        estado: filterEstado || undefined,
      }).then((r) => r.data),
  });

  // When a ticket is selected, fetch latest version
  const { data: ticketDetalle } = useQuery<TicketPQRS>({
    queryKey: ['pqrs', selectedTicket?.id],
    queryFn: () => pqrs.get(selectedTicket!.id).then((r) => r.data),
    enabled: !!selectedTicket,
  });

  if (selectedTicket && ticketDetalle) {
    return (
      <div>
        <TicketDetail
          ticket={ticketDetalle}
          onBack={() => setSelectedTicket(null)}
        />
      </div>
    );
  }

  return (
    <div>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <h1 className="font-brand text-xl font-medium cv-text">Soporte</h1>
        <button onClick={() => setShowCreate(true)} className="cv-btn cv-btn-primary">
          + Nuevo ticket
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <select
          value={filterTipo}
          onChange={(e) => setFilterTipo(e.target.value as TipoPQRS | '')}
          className="cv-input w-auto"
        >
          <option value="">Todos los tipos</option>
          <option value="SOPORTE">Soporte</option>
          <option value="PETICION">Petición</option>
          <option value="QUEJA">Queja</option>
          <option value="RECLAMO">Reclamo</option>
          <option value="SUGERENCIA">Sugerencia</option>
        </select>

        <select
          value={filterEstado}
          onChange={(e) => setFilterEstado(e.target.value as EstadoTicket | '')}
          className="cv-input w-auto"
        >
          <option value="">Todos los estados</option>
          <option value="ABIERTO">Abierto</option>
          <option value="EN_PROCESO">En proceso</option>
          <option value="RESUELTO">Resuelto</option>
          <option value="CERRADO">Cerrado</option>
        </select>
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 cv-elevated rounded-lg animate-pulse" />
          ))}
        </div>
      ) : (
        <TicketList tickets={tickets} onSelect={setSelectedTicket} />
      )}

      <CreateTicketModal open={showCreate} onClose={() => setShowCreate(false)} />
    </div>
  );
}
