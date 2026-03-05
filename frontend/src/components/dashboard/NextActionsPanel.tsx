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

  // Ventas pendientes de facturar
  if (pipeline.ventas_pendientes.length > 0) {
    const totalPendiente = pipeline.ventas_pendientes.reduce(
      (s, v) => s + Number(v.total_venta ?? 0), 0
    );
    actions.push({
      id: 'ventas-pendientes',
      mensaje: `${pipeline.ventas_pendientes.length} venta${pipeline.ventas_pendientes.length > 1 ? 's' : ''} por facturar (${formatCurrency(totalPendiente)})`,
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
  alta:   { badge: 'bg-red-100 text-red-700',    border: 'border-l-red-400' },
  media:  { badge: 'bg-amber-100 text-amber-700', border: 'border-l-amber-400' },
  normal: { badge: 'bg-blue-50 text-blue-600',   border: 'border-l-blue-300' },
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
      <p className="text-xs font-semibold uppercase tracking-wider text-gray-400 mb-2">
        Próximas acciones
      </p>
      <div className="space-y-2">
        {actions.map((action) => {
          const styles = URGENCIA_STYLES[action.urgencia];
          return (
            <div
              key={action.id}
              className={`flex items-center justify-between gap-3 rounded-xl bg-white border border-gray-100 border-l-4 ${styles.border} px-4 py-3 shadow-sm`}
            >
              <p className="text-sm text-gray-700">{action.mensaje}</p>
              <Link
                to={action.to}
                className={`shrink-0 rounded-lg px-3 py-1.5 text-xs font-semibold transition-colors ${styles.badge}`}
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
