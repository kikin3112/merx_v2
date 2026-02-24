import { useState, type FormEvent } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { pqrs } from '../../api/endpoints';
import Modal from '../ui/Modal';
import type { TipoPQRS, PrioridadTicket } from '../../types';

interface CreateTicketModalProps {
  open: boolean;
  onClose: () => void;
}

export default function CreateTicketModal({ open, onClose }: CreateTicketModalProps) {
  const queryClient = useQueryClient();
  const [tipo, setTipo] = useState<TipoPQRS>('SOPORTE');
  const [asunto, setAsunto] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [prioridad, setPrioridad] = useState<PrioridadTicket>('MEDIA');
  const [error, setError] = useState('');

  const createMutation = useMutation({
    mutationFn: () => pqrs.create({ tipo, asunto: asunto.trim(), descripcion: descripcion.trim(), prioridad }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pqrs'] });
      setAsunto('');
      setDescripcion('');
      setTipo('SOPORTE');
      setPrioridad('MEDIA');
      setError('');
      onClose();
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(detail || 'Error al crear ticket');
    },
  });

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (!asunto.trim()) { setError('El asunto es requerido'); return; }
    if (descripcion.trim().length < 10) { setError('La descripción debe tener al menos 10 caracteres'); return; }
    setError('');
    createMutation.mutate();
  };

  const inputClass =
    'w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:ring-2 focus:ring-primary-500/20 outline-none';

  return (
    <Modal open={open} onClose={onClose} title="Nuevo Ticket de Soporte">
      <form onSubmit={handleSubmit} className="space-y-4">
        {error && (
          <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <select value={tipo} onChange={(e) => setTipo(e.target.value as TipoPQRS)} className={inputClass}>
              <option value="SOPORTE">Soporte</option>
              <option value="PETICION">Petición</option>
              <option value="QUEJA">Queja</option>
              <option value="RECLAMO">Reclamo</option>
              <option value="SUGERENCIA">Sugerencia</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Prioridad</label>
            <select value={prioridad} onChange={(e) => setPrioridad(e.target.value as PrioridadTicket)} className={inputClass}>
              <option value="BAJA">Baja</option>
              <option value="MEDIA">Media</option>
              <option value="ALTA">Alta</option>
              <option value="CRITICA">Crítica</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Asunto *</label>
          <input
            type="text"
            value={asunto}
            onChange={(e) => setAsunto(e.target.value)}
            required
            maxLength={300}
            className={inputClass}
            placeholder="Describe brevemente tu solicitud"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Descripción *</label>
          <textarea
            value={descripcion}
            onChange={(e) => setDescripcion(e.target.value)}
            required
            rows={5}
            className={`${inputClass} resize-none`}
            placeholder="Describe detalladamente tu solicitud o problema (mínimo 10 caracteres)"
          />
        </div>

        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 transition-colors"
          >
            Cancelar
          </button>
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="rounded-lg bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {createMutation.isPending ? 'Creando...' : 'Crear Ticket'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
