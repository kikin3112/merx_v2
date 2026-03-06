import { useState } from 'react';
import type { CrmDeal, CrmStage } from '../../types';

interface KanbanBoardProps {
  stages: CrmStage[];
  deals: CrmDeal[];
  onDealClick: (deal: CrmDeal) => void;
  onDealMove: (dealId: string, newStageId: string) => void;
}

export default function KanbanBoard({
  stages,
  deals,
  onDealClick,
  onDealMove,
}: KanbanBoardProps) {
  const [draggedDealId, setDraggedDealId] = useState<string | null>(null);

  // Agrupar deals por stage
  const dealsByStage = stages.reduce((acc, stage) => {
    acc[stage.id] = deals.filter((deal) => deal.stage_id === stage.id);
    return acc;
  }, {} as Record<string, CrmDeal[]>);

  // Handlers drag & drop
  const handleDragStart = (dealId: string) => {
    setDraggedDealId(dealId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (stageId: string) => {
    if (draggedDealId && draggedDealId !== stageId) {
      onDealMove(draggedDealId, stageId);
    }
    setDraggedDealId(null);
  };

  // Formatear moneda
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('es-CO', {
      style: 'currency',
      currency: 'COP',
      minimumFractionDigits: 0,
    }).format(value);
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {stages
        .sort((a, b) => a.orden - b.orden)
        .map((stage) => (
          <div
            key={stage.id}
            className="cv-card flex-shrink-0 w-80 p-4"
            onDragOver={handleDragOver}
            onDrop={() => handleDrop(stage.id)}
          >
            {/* Stage Header */}
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-sm font-semibold cv-text">{stage.nombre}</h3>
                <p className="text-xs cv-muted">
                  {dealsByStage[stage.id]?.length || 0} deals · {stage.probabilidad}%
                </p>
              </div>
              {/* Badge con probabilidad */}
              <span
                className="px-2 py-1 text-xs font-medium rounded"
                style={{
                  backgroundColor: `rgba(255, 155, 101, ${stage.probabilidad / 100 * 0.8})`,
                  color: stage.probabilidad > 50 ? 'white' : 'var(--cv-text)',
                }}
              >
                {stage.probabilidad}%
              </span>
            </div>

            {/* Deals List */}
            <div className="space-y-3">
              {dealsByStage[stage.id]?.length === 0 ? (
                <div className="text-center py-8 text-sm cv-muted">
                  No hay deals en esta etapa
                </div>
              ) : (
                dealsByStage[stage.id]?.map((deal) => (
                  <div
                    key={deal.id}
                    draggable
                    onDragStart={() => handleDragStart(deal.id)}
                    onClick={() => onDealClick(deal)}
                    className={`cv-card p-4 cursor-move hover:shadow-md transition-shadow ${
                      draggedDealId === deal.id ? 'opacity-50' : ''
                    }`}
                  >
                    {/* Deal Header */}
                    <div className="flex items-start justify-between mb-2">
                      <h4 className="text-sm font-medium cv-text line-clamp-2">
                        {deal.nombre}
                      </h4>
                      {deal.estado_cierre !== 'ABIERTO' && (
                        <span
                          className={`cv-badge ${
                            deal.estado_cierre === 'GANADO'
                              ? 'cv-badge-positive'
                              : deal.estado_cierre === 'PERDIDO'
                              ? 'cv-badge-negative'
                              : 'cv-badge-neutral'
                          }`}
                        >
                          {deal.estado_cierre}
                        </span>
                      )}
                    </div>

                    {/* Cliente */}
                    {deal.tercero_nombre && (
                      <p className="text-xs cv-muted mb-2">
                        👤 {deal.tercero_nombre}
                      </p>
                    )}

                    {/* Valor estimado */}
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold" style={{ color: 'var(--cv-primary)' }}>
                        {formatCurrency(deal.valor_estimado)}
                      </span>
                      {deal.usuario_nombre && (
                        <span className="text-xs cv-muted">
                          {deal.usuario_nombre.split(' ')[0]}
                        </span>
                      )}
                    </div>

                    {/* Fecha cierre estimada */}
                    {deal.fecha_cierre_estimada && (
                      <p className="text-xs cv-muted mt-2">
                        📅{' '}
                        {new Date(deal.fecha_cierre_estimada).toLocaleDateString('es-CO', {
                          day: 'numeric',
                          month: 'short',
                        })}
                      </p>
                    )}
                  </div>
                ))
              )}
            </div>

            {/* Total Stage */}
            {dealsByStage[stage.id]?.length > 0 && (
              <div className="mt-4 pt-3 border-t border-[var(--cv-divider)]">
                <div className="flex items-center justify-between text-sm">
                  <span className="cv-muted font-medium">Total:</span>
                  <span className="cv-text font-semibold">
                    {formatCurrency(
                      dealsByStage[stage.id]?.reduce(
                        (sum, deal) => sum + deal.valor_estimado,
                        0
                      ) || 0
                    )}
                  </span>
                </div>
              </div>
            )}
          </div>
        ))}
    </div>
  );
}
