"""
Servicio de Costos Indirectos.
Gestiona los costos fijos y porcentuales que se prorratean entre recetas.
"""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from ..datos.modelos import CostosIndirectos, TipoCostoIndirecto
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioCostosIndirectos:
    """
    Gestiona los costos indirectos de producción de un tenant.
    Permite crear, listar, actualizar y eliminar costos indirectos,
    y calcular el total de costos indirectos para un costo base dado.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def listar(self, solo_activos: bool = True) -> List[CostosIndirectos]:
        """Lista todos los costos indirectos del tenant."""
        q = self.db.query(CostosIndirectos).filter(
            CostosIndirectos.tenant_id == self.tenant_id,
            CostosIndirectos.deleted_at.is_(None),
        )
        if solo_activos:
            q = q.filter(CostosIndirectos.activo.is_(True))
        return q.order_by(CostosIndirectos.nombre).all()

    def obtener(self, costo_id: UUID) -> Optional[CostosIndirectos]:
        """Obtiene un costo indirecto por ID."""
        return (
            self.db.query(CostosIndirectos)
            .filter(
                CostosIndirectos.id == costo_id,
                CostosIndirectos.tenant_id == self.tenant_id,
                CostosIndirectos.deleted_at.is_(None),
            )
            .first()
        )

    def crear(self, nombre: str, monto: Decimal, tipo: TipoCostoIndirecto, user_id: UUID) -> CostosIndirectos:
        """Crea un nuevo costo indirecto."""
        costo = CostosIndirectos(
            tenant_id=self.tenant_id,
            nombre=nombre,
            monto=monto,
            tipo=tipo,
            activo=True,
            created_by=user_id,
            updated_by=user_id,
        )
        self.db.add(costo)
        self.db.commit()
        self.db.refresh(costo)
        logger.info("Costo indirecto creado", extra={"tenant_id": str(self.tenant_id), "id": str(costo.id)})
        return costo

    def actualizar(
        self,
        costo_id: UUID,
        nombre: Optional[str],
        monto: Optional[Decimal],
        tipo: Optional[TipoCostoIndirecto],
        activo: Optional[bool],
        user_id: UUID,
    ) -> CostosIndirectos:
        """Actualiza un costo indirecto existente."""
        costo = self.obtener(costo_id)
        if not costo:
            raise ValueError("Costo indirecto no encontrado")

        if nombre is not None:
            costo.nombre = nombre
        if monto is not None:
            costo.monto = monto
        if tipo is not None:
            costo.tipo = tipo
        if activo is not None:
            costo.activo = activo
        costo.updated_by = user_id

        self.db.commit()
        self.db.refresh(costo)
        return costo

    def eliminar(self, costo_id: UUID, user_id: UUID) -> None:
        """Soft delete de un costo indirecto."""

        costo = self.obtener(costo_id)
        if not costo:
            raise ValueError("Costo indirecto no encontrado")

        costo.soft_delete(user_id=user_id)
        self.db.commit()

    def calcular_total_para_costo_base(self, costo_base: Decimal) -> tuple[Decimal, List[dict]]:
        """
        Calcula el total de costos indirectos activos para un costo base dado.

        - FIJO: se suma el monto directamente (COP por unidad)
        - PORCENTAJE: se aplica el % sobre el costo_base

        Returns:
            tuple (total_indirecto: Decimal, detalle: List[dict])
        """
        costos = self.listar(solo_activos=True)
        total = Decimal("0.00")
        detalle = []

        for c in costos:
            if c.tipo == TipoCostoIndirecto.FIJO:
                monto_aplicado = c.monto
            else:  # PORCENTAJE
                monto_aplicado = (costo_base * c.monto / 100).quantize(Decimal("0.01"))

            total += monto_aplicado
            detalle.append(
                {
                    "id": str(c.id),
                    "nombre": c.nombre,
                    "tipo": c.tipo.value,
                    "monto_configurado": c.monto,
                    "monto_aplicado": monto_aplicado,
                }
            )

        return total, detalle

    def calcular_fijo_y_porcentaje(self, costo_base: Decimal) -> tuple[Decimal, Decimal]:
        """
        Separa el CIF en dos componentes:
        - fijo_total: suma de todos los costos FIJO (monto mensual fijo, ej. arriendo)
        - porcentaje_total: suma de % aplicados sobre costo_base (variable con el lote)

        Usado para distribuir el CIF fijo entre la producción mensual real.

        Returns:
            (fijo_total, porcentaje_total)
        """
        costos = self.listar(solo_activos=True)
        fijo_total = Decimal("0.00")
        porcentaje_total = Decimal("0.00")

        for c in costos:
            if c.tipo == TipoCostoIndirecto.FIJO:
                fijo_total += c.monto
            else:  # PORCENTAJE
                porcentaje_total += (costo_base * c.monto / 100).quantize(Decimal("0.01"))

        return fijo_total, porcentaje_total
