import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { XMarkIcon } from '@heroicons/react/24/outline';
import { crm } from '../../api/endpoints';
import type { CrmDeal, TipoActividadCRM } from '../../types';
import ActivityFeed from './ActivityFeed';

interface DealDetailModalProps {
  deal: CrmDeal;
  onClose: () => void;
  onUpdate?: () => void;
}

export default function DealDetailModal({ deal, onClose, onUpdate }: DealDetailModalProps) {
  const queryClient = useQueryClient();
  const [isAddingNote, setIsAddingNote] = useState(false);
  const [noteContent, setNoteContent] = useState('');
  const [noteSubject, setNoteSubject] = useState('');
  const [selectedActivityType, setSelectedActivityType] = useState<TipoActividadCRM>('NOTA');

  // Fetch activities
  const { data: activities, isLoading: loadingActivities } = useQuery({
    queryKey: ['crm-activities', deal.id],
    queryFn: () => crm.activities.list(deal.id).then((r) => r.data),
  });

  // Create activity mutation
  const createActivityMut = useMutation({
    mutationFn: (data: { tipo: TipoActividadCRM; asunto: string; contenido: string }) =>
      crm.activities.create(deal.id, {
        deal_id: deal.id,
        tipo: data.tipo,
        asunto: data.asunto,
        contenido: data.contenido,
        fecha_actividad: new Date().toISOString(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-activities', deal.id] });
      queryClient.invalidateQueries({ queryKey: ['crm-deals'] });
      setNoteContent('');
      setNoteSubject('');
      setIsAddingNote(false);
      if (onUpdate) onUpdate();
    },
  });

  // Close deal mutation
  const closeDealMut = useMutation({
    mutationFn: (data: { estado: string; motivo?: string }) =>
      crm.deals.close(deal.id, data.estado, data.motivo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['crm-deals'] });
      if (onUpdate) onUpdate();
    },
  });

  const handleAddNote = () => {
    if (!noteContent.trim()) return;

    createActivityMut.mutate({
      tipo: selectedActivityType,
      asunto: noteSubject || `${selectedActivityType} - ${new Date().toLocaleDateString()}`,
      contenido: noteContent,
    });
  };

  const handleCloseDeal = (estado: 'GANADO' | 'PERDIDO' | 'ABANDONADO') => {
    const motivo = prompt(
      `¿Motivo de cierre como ${estado}?`,
      estado === 'GANADO' ? 'Cliente aceptó propuesta' : 'Cliente no interesado'
    );
    if (motivo !== null) {
      closeDealMut.mutate({ estado, motivo });
    }
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-start justify-between p-6 border-b border-gray-200">
          <div className="flex-1">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{deal.nombre}</h2>
            <div className="flex items-center gap-3 text-sm text-gray-600">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full font-medium">
                {deal.stage_nombre}
              </span>
              <span className="font-semibold text-blue-600 text-lg">
                {formatCurrency(deal.valor_estimado)}
              </span>
              {deal.estado_cierre !== 'ABIERTO' && (
                <span
                  className={`px-3 py-1 rounded-full font-medium ${
                    deal.estado_cierre === 'GANADO'
                      ? 'bg-green-100 text-green-800'
                      : deal.estado_cierre === 'PERDIDO'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {deal.estado_cierre}
                </span>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-3 gap-6">
            {/* Left Panel - Deal Info */}
            <div className="col-span-1 space-y-6">
              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Información del Cliente</h3>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="text-gray-600">Nombre:</span>{' '}
                    <span className="font-medium">{deal.tercero_nombre || 'N/A'}</span>
                  </p>
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold text-gray-900 mb-3">Datos del Deal</h3>
                <div className="space-y-2 text-sm">
                  <p>
                    <span className="text-gray-600">Valor:</span>{' '}
                    <span className="font-medium">{formatCurrency(deal.valor_estimado)}</span>
                  </p>
                  {deal.fecha_cierre_estimada && (
                    <p>
                      <span className="text-gray-600">Cierre estimado:</span>{' '}
                      <span className="font-medium">
                        {new Date(deal.fecha_cierre_estimada).toLocaleDateString('es-CO')}
                      </span>
                    </p>
                  )}
                  {deal.usuario_nombre && (
                    <p>
                      <span className="text-gray-600">Dueño:</span>{' '}
                      <span className="font-medium">{deal.usuario_nombre}</span>
                    </p>
                  )}
                  {deal.origen && (
                    <p>
                      <span className="text-gray-600">Origen:</span>{' '}
                      <span className="font-medium">{deal.origen}</span>
                    </p>
                  )}
                  {deal.fecha_ultimo_contacto && (
                    <p>
                      <span className="text-gray-600">Último contacto:</span>{' '}
                      <span className="font-medium">
                        {new Date(deal.fecha_ultimo_contacto).toLocaleDateString('es-CO')}
                      </span>
                    </p>
                  )}
                </div>
              </div>

              {/* Actions */}
              {deal.estado_cierre === 'ABIERTO' && (
                <div>
                  <h3 className="text-sm font-semibold text-gray-900 mb-3">Acciones</h3>
                  <div className="space-y-2">
                    <button
                      onClick={() => handleCloseDeal('GANADO')}
                      disabled={closeDealMut.isPending}
                      className="w-full px-3 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 disabled:opacity-50"
                    >
                      ✓ Marcar como Ganado
                    </button>
                    <button
                      onClick={() => handleCloseDeal('PERDIDO')}
                      disabled={closeDealMut.isPending}
                      className="w-full px-3 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 disabled:opacity-50"
                    >
                      ✗ Marcar como Perdido
                    </button>
                    <button
                      onClick={() => handleCloseDeal('ABANDONADO')}
                      disabled={closeDealMut.isPending}
                      className="w-full px-3 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700 disabled:opacity-50"
                    >
                      Marcar como Abandonado
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Right Panel - Activity Feed */}
            <div className="col-span-2 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-gray-900">Actividades</h3>
                <button
                  onClick={() => setIsAddingNote(!isAddingNote)}
                  className="px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700"
                >
                  {isAddingNote ? 'Cancelar' : '+ Agregar Actividad'}
                </button>
              </div>

              {/* Add Activity Form */}
              {isAddingNote && (
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo
                    </label>
                    <select
                      value={selectedActivityType}
                      onChange={(e) => setSelectedActivityType(e.target.value as TipoActividadCRM)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="NOTA">Nota</option>
                      <option value="LLAMADA">Llamada</option>
                      <option value="EMAIL">Email</option>
                      <option value="REUNION">Reunión</option>
                      <option value="WHATSAPP">WhatsApp</option>
                      <option value="TAREA">Tarea</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Asunto
                    </label>
                    <input
                      type="text"
                      value={noteSubject}
                      onChange={(e) => setNoteSubject(e.target.value)}
                      placeholder="Asunto de la actividad"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Contenido
                    </label>
                    <textarea
                      value={noteContent}
                      onChange={(e) => setNoteContent(e.target.value)}
                      placeholder="Describe la actividad..."
                      rows={3}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <button
                    onClick={handleAddNote}
                    disabled={createActivityMut.isPending || !noteContent.trim()}
                    className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50"
                  >
                    {createActivityMut.isPending ? 'Guardando...' : 'Guardar Actividad'}
                  </button>
                </div>
              )}

              {/* Activity Feed */}
              {loadingActivities ? (
                <div className="text-center py-8 text-gray-500">Cargando actividades...</div>
              ) : (
                <ActivityFeed activities={activities || []} />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
