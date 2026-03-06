/**
 * FASE 05 — Next Actions Panel
 * Muestra sugerencias de próxima acción basadas en el pipeline comercial.
 * Zero-fluff: solo muestra algo si hay acciones concretas.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { comercial } from '../../api/endpoints';
import { formatCurrency } from '../../utils/format';
import type { Cotizacion, Venta } from '../../types';

interface PipelineData {
  cotizaciones: Cotizacion[];
  ventas_pendientes: Venta[];
  ventas_confirmadas: Venta[];
  facturas_recientes: Venta[];
  resumen: { total_cotizado: string; por_cobrar: string; facturado_mes: string };
}

interface Action {
  id: string;
  mensaje: string;
  cta: string;
  to: string;
  urgencia: 'alta' | 'media' | 'normal';
}

function buildActions(pipeline: PipelineData): Action[] {
  const actions: Action[] = [];
  const hoy = new Date();

  // Cotizaciones vigentes >3 días sin conversión
  const cotsPendientes = pipeline.cotizaciones.filter((c) => {
    const dias = (hoy.getTime() - new Date(c.fecha_cotizacion).getTime()) / 86_400_000;
    return c.estado === 'VIGENTE' && dias > 3;
  });
  if (cotsPendientes.length > 0) {
    actions.push({
      id: 'cots-pendientes',
      mensaje: `${cotsPendientes.length} cotización${cotsPendientes.length > 1 ? 'es' : ''} lleva${cotsPendientes.length > 1 ? 'n' : ''} más de 3 días esperando`,
      cta: 'Revisar pipeline',
      to: '/comercial',
      urgencia: 'media',
    });
  }

  // Ventas en borrador (sin confirmar)
  if (pipeline.ventas_pendientes.length > 0) {
    actions.push({
      id: 'ventas-sin-confirmar',
      mensaje: `${pipeline.ventas_pendientes.length} venta${pipeline.ventas_pendientes.length > 1 ? 's' : ''} sin confirmar`,
      cta: 'Confirmar',
      to: '/ventas',
      urgencia: 'media',
    });
  }

  // Ventas confirmadas → pendientes de emitir factura
  if (pipeline.ventas_confirmadas.length > 0) {
    const totalConfirmadas = pipeline.ventas_confirmadas.reduce(
      (s, v) => s + Number(v.total_venta ?? 0), 0
    );
    actions.push({
      id: 'ventas-por-facturar',
      mensaje: `${pipeline.ventas_confirmadas.length} venta${pipeline.ventas_confirmadas.length > 1 ? 's' : ''} por facturar (${formatCurrency(totalConfirmadas)})`,
      cta: 'Facturar ahora',
      to: '/comercial',
      urgencia: 'alta',
    });
  }

  // Facturas vencidas (>30 días sin indicación de pago)
  const facturasViejas = pipeline.facturas_recientes.filter((f) => {
    const dias = (hoy.getTime() - new Date(f.fecha_venta).getTime()) / 86_400_000;
    return dias > 30;
  });
  if (facturasViejas.length > 0) {
    const totalVencido = facturasViejas.reduce(
      (s, v) => s + Number(v.total_venta ?? 0), 0
    );
    actions.push({
      id: 'facturas-vencidas',
      mensaje: `${facturasViejas.length} factura${facturasViejas.length > 1 ? 's' : ''} con más de 30 días (${formatCurrency(totalVencido)})`,
      cta: 'Ir a cartera',
      to: '/cartera',
      urgencia: 'alta',
    });
  }

  return actions;
}

const URGENCIA_STYLES: Record<string, { badge: string; border: string }> = {
  alta:   { badge: 'cv-badge cv-badge-negative',  border: 'border-l-[var(--cv-negative)]' },
  media:  { badge: 'cv-badge cv-badge-accent',    border: 'border-l-[var(--cv-accent)]' },
  normal: { badge: 'cv-badge cv-badge-primary',   border: 'border-l-[var(--cv-primary)]' },
};

export default function NextActionsPanel() {
  const { data: pipeline, isLoading } = useQuery<PipelineData>({
    queryKey: ['comercial-pipeline'],
    queryFn: () => comercial.pipeline().then((r) => r.data),
    staleTime: 60_000,
  });

  if (isLoading || !pipeline) return null;

  const actions = buildActions(pipeline);
  if (actions.length === 0) return null;

  return (
    <div className="mb-4">
      <p className="cv-section-label mb-2">
        Próximas acciones
      </p>
      <div className="space-y-2">
        {actions.map((action) => {
          const styles = URGENCIA_STYLES[action.urgencia];
          return (
            <div
              key={action.id}
              className={`flex items-center justify-between gap-3 cv-card border-l-4 ${styles.border} px-4 py-3`}
            >
              <p className="text-sm cv-text">{action.mensaje}</p>
              <Link
                to={action.to}
                className={`shrink-0 ${styles.badge}`}
              >
                {action.cta}
              </Link>
            </div>
          );
        })}
      </div>
    </div>
  );
}
