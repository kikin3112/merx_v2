"""
Servicio Comercial — Pipeline unificado de cotizaciones, ventas y facturas.
Agrega datos de múltiples módulos para la vista ComercialPage del frontend.
"""

from datetime import date
from decimal import Decimal
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from ..datos.modelos import Cotizaciones, Ventas


class ServicioComercial:
    """Orquestador del pipeline comercial unificado."""

    def obtener_pipeline(self, db: Session, tenant_id: UUID) -> Dict[str, Any]:
        """
        Retorna el estado completo del pipeline comercial del tenant.
        Consultas paralelas usando el mismo hilo de DB (SQLAlchemy sync).
        """
        cotizaciones = self._get_cotizaciones(db, tenant_id)
        ventas_pendientes = self._get_ventas_por_estado(db, tenant_id, ["PENDIENTE"])
        ventas_confirmadas = self._get_ventas_por_estado(db, tenant_id, ["CONFIRMADA"])
        facturas_recientes = self._get_facturas_recientes(db, tenant_id)

        total_cotizado = sum(c.total_cotizacion for c in cotizaciones if c.total_cotizacion)
        por_cobrar = sum(v.total_venta for v in facturas_recientes if v.total_venta and v.estado == "FACTURADA")
        facturado_mes = self._total_facturado_mes(db, tenant_id)

        return {
            "cotizaciones": cotizaciones,
            "ventas_pendientes": ventas_pendientes,
            "ventas_confirmadas": ventas_confirmadas,
            "facturas_recientes": facturas_recientes,
            "resumen": {
                "total_cotizado": str(total_cotizado),
                "por_cobrar": str(por_cobrar),
                "facturado_mes": str(facturado_mes),
            },
        }

    def _get_cotizaciones(self, db: Session, tenant_id: UUID) -> List[Cotizaciones]:
        return (
            db.query(Cotizaciones)
            .filter(
                Cotizaciones.tenant_id == tenant_id,
                Cotizaciones.estado.in_(["VIGENTE", "PENDIENTE"]),
            )
            .order_by(Cotizaciones.created_at.desc())
            .limit(50)
            .all()
        )

    def _get_ventas_por_estado(self, db: Session, tenant_id: UUID, estados: List[str]) -> List[Ventas]:
        return (
            db.query(Ventas)
            .filter(
                Ventas.tenant_id == tenant_id,
                Ventas.estado.in_(estados),
            )
            .order_by(Ventas.created_at.desc())
            .limit(50)
            .all()
        )

    def _get_facturas_recientes(self, db: Session, tenant_id: UUID) -> List[Ventas]:
        return (
            db.query(Ventas)
            .filter(
                Ventas.tenant_id == tenant_id,
                Ventas.estado == "FACTURADA",
            )
            .order_by(Ventas.created_at.desc())
            .limit(30)
            .all()
        )

    def _total_facturado_mes(self, db: Session, tenant_id: UUID) -> Decimal:
        from sqlalchemy import extract

        hoy = date.today()
        # total_venta is a hybrid property computed from detalles — cannot use in SQL aggregate.
        # Load instances and sum in Python instead.
        ventas = (
            db.query(Ventas)
            .filter(
                Ventas.tenant_id == tenant_id,
                Ventas.estado == "FACTURADA",
                extract("year", Ventas.created_at) == hoy.year,
                extract("month", Ventas.created_at) == hoy.month,
            )
            .all()
        )
        return sum((v.total_venta for v in ventas), Decimal("0"))
