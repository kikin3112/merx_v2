"""
Servicio de Contabilidad - Lógica para asientos contables automáticos y manuales.
"""

from decimal import Decimal
from datetime import date
from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func

from ..datos.modelos import (
    AsientosContables, DetallesAsiento, CuentasContables,
    ConfiguracionContable, Usuarios
)
from ..datos.esquemas import AsientoContableCreate
from ..utils.secuencia_helper import generar_numero_secuencia
from ..utils.logger import setup_logger

logger = setup_logger(__name__)


class ServicioContabilidad:
    """Servicio para operaciones contables."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _obtener_cuenta_por_codigo(self, codigo: str) -> Optional[CuentasContables]:
        """Obtiene una cuenta contable por código."""
        return self.db.query(CuentasContables).filter(
            CuentasContables.tenant_id == self.tenant_id,
            CuentasContables.codigo == codigo
        ).first()

    def crear_asiento(
        self,
        fecha: date,
        tipo_asiento: str,
        concepto: str,
        detalles: List[dict],
        documento_referencia: Optional[str] = None
    ) -> AsientosContables:
        """
        Crea un asiento contable validando que esté balanceado.

        Args:
            fecha: Fecha del asiento
            tipo_asiento: VENTAS, COMPRAS, PRODUCCION, AJUSTE, etc.
            concepto: Descripción del asiento
            detalles: Lista de dicts con {cuenta_id, debito, credito, descripcion}
            documento_referencia: Número de documento origen

        Returns:
            AsientoContable creado

        Raises:
            ValueError: Si el asiento no está balanceado o faltan datos
        """
        if not detalles:
            raise ValueError("El asiento debe tener al menos una línea")

        # Validar balance
        total_debito = sum(Decimal(str(d.get("debito", 0))) for d in detalles)
        total_credito = sum(Decimal(str(d.get("credito", 0))) for d in detalles)

        if total_debito != total_credito:
            raise ValueError(
                f"Asiento desbalanceado: Débitos={total_debito}, Créditos={total_credito}"
            )

        if total_debito == 0:
            raise ValueError("El asiento no puede tener todos los valores en cero")

        # Generar número
        numero = generar_numero_secuencia(self.db, 'ASIENTOS', self.tenant_id)

        asiento = AsientosContables(
            tenant_id=self.tenant_id,
            numero_asiento=numero,
            fecha=fecha,
            tipo_asiento=tipo_asiento,
            concepto=concepto,
            documento_referencia=documento_referencia,
            estado="ACTIVO"
        )
        self.db.add(asiento)
        self.db.flush()

        for det in detalles:
            # Validar que la cuenta existe
            cuenta = self.db.query(CuentasContables).filter(
                CuentasContables.id == det["cuenta_id"],
                CuentasContables.tenant_id == self.tenant_id
            ).first()
            if not cuenta:
                raise ValueError(f"Cuenta contable {det['cuenta_id']} no encontrada")

            detalle = DetallesAsiento(
                tenant_id=self.tenant_id,
                asiento_id=asiento.id,
                cuenta_id=det["cuenta_id"],
                debito=Decimal(str(det.get("debito", 0))),
                credito=Decimal(str(det.get("credito", 0))),
                descripcion=det.get("descripcion", "")
            )
            self.db.add(detalle)

        self.db.flush()

        logger.info(
            f"Asiento {numero} creado - Tipo: {tipo_asiento}, Total: {total_debito}"
        )

        return asiento

    def crear_asiento_venta(
        self,
        fecha: date,
        subtotal: Decimal,
        total_iva: Decimal,
        total: Decimal,
        documento_referencia: str
    ) -> Optional[AsientosContables]:
        """
        Crea asiento contable automático para una venta/factura.

        DEBE: 1105 Caja (total)
        HABER: 4135 Comercio (subtotal)
        HABER: 2408 IVA por pagar (iva) -- si hay IVA
        """
        cuenta_caja = self._obtener_cuenta_por_codigo("1105")
        cuenta_ventas = self._obtener_cuenta_por_codigo("4135")
        cuenta_iva = self._obtener_cuenta_por_codigo("2408")

        if not cuenta_caja or not cuenta_ventas:
            logger.warning(
                f"No se puede crear asiento de venta: faltan cuentas contables "
                f"(1105={'OK' if cuenta_caja else 'FALTA'}, "
                f"4135={'OK' if cuenta_ventas else 'FALTA'})"
            )
            return None

        # Ingresos netos = total - IVA (garantiza balance con descuentos globales/línea)
        ingresos_netos = total - total_iva

        detalles = [
            {
                "cuenta_id": cuenta_caja.id,
                "debito": total,
                "credito": Decimal("0"),
                "descripcion": f"Cobro venta {documento_referencia}"
            },
            {
                "cuenta_id": cuenta_ventas.id,
                "debito": Decimal("0"),
                "credito": ingresos_netos,
                "descripcion": f"Venta {documento_referencia}"
            }
        ]

        if total_iva > 0 and cuenta_iva:
            detalles.append({
                "cuenta_id": cuenta_iva.id,
                "debito": Decimal("0"),
                "credito": total_iva,
                "descripcion": f"IVA venta {documento_referencia}"
            })

        return self.crear_asiento(
            fecha=fecha,
            tipo_asiento="VENTAS",
            concepto=f"Venta según {documento_referencia}",
            detalles=detalles,
            documento_referencia=documento_referencia
        )

    def crear_asiento_anulacion_venta(
        self,
        fecha: date,
        subtotal: Decimal,
        total_iva: Decimal,
        total: Decimal,
        documento_referencia: str
    ) -> Optional[AsientosContables]:
        """
        Crea asiento contable de reversión para anulación de venta.
        Invierte el asiento original.
        """
        cuenta_caja = self._obtener_cuenta_por_codigo("1105")
        cuenta_ventas = self._obtener_cuenta_por_codigo("4135")
        cuenta_iva = self._obtener_cuenta_por_codigo("2408")

        if not cuenta_caja or not cuenta_ventas:
            return None

        # Ingresos netos = total - IVA (garantiza balance con descuentos globales/línea)
        ingresos_netos = total - total_iva

        detalles = [
            {
                "cuenta_id": cuenta_caja.id,
                "debito": Decimal("0"),
                "credito": total,
                "descripcion": f"Anulación venta {documento_referencia}"
            },
            {
                "cuenta_id": cuenta_ventas.id,
                "debito": ingresos_netos,
                "credito": Decimal("0"),
                "descripcion": f"Anulación venta {documento_referencia}"
            }
        ]

        if total_iva > 0 and cuenta_iva:
            detalles.append({
                "cuenta_id": cuenta_iva.id,
                "debito": total_iva,
                "credito": Decimal("0"),
                "descripcion": f"Anulación IVA venta {documento_referencia}"
            })

        return self.crear_asiento(
            fecha=fecha,
            tipo_asiento="VENTAS",
            concepto=f"Anulación venta {documento_referencia}",
            detalles=detalles,
            documento_referencia=f"ANUL-{documento_referencia}"
        )

    def obtener_balance_prueba(
        self,
        fecha_inicio: Optional[date] = None,
        fecha_fin: Optional[date] = None
    ) -> List[dict]:
        """
        Genera balance de prueba: para cada cuenta, suma débitos y créditos.
        """
        query = self.db.query(
            CuentasContables.id,
            CuentasContables.codigo,
            CuentasContables.nombre,
            CuentasContables.tipo_cuenta,
            CuentasContables.naturaleza,
            func.coalesce(func.sum(DetallesAsiento.debito), 0).label("total_debito"),
            func.coalesce(func.sum(DetallesAsiento.credito), 0).label("total_credito")
        ).outerjoin(
            DetallesAsiento,
            (DetallesAsiento.cuenta_id == CuentasContables.id) &
            (DetallesAsiento.tenant_id == self.tenant_id)
        ).outerjoin(
            AsientosContables,
            (AsientosContables.id == DetallesAsiento.asiento_id) &
            (AsientosContables.estado == "ACTIVO")
        ).filter(
            CuentasContables.tenant_id == self.tenant_id,
            CuentasContables.acepta_movimiento == True
        )

        if fecha_inicio:
            query = query.filter(AsientosContables.fecha >= fecha_inicio)
        if fecha_fin:
            query = query.filter(AsientosContables.fecha <= fecha_fin)

        query = query.group_by(
            CuentasContables.id,
            CuentasContables.codigo,
            CuentasContables.nombre,
            CuentasContables.tipo_cuenta,
            CuentasContables.naturaleza
        ).order_by(CuentasContables.codigo)

        resultados = []
        for row in query.all():
            total_debito = Decimal(str(row.total_debito))
            total_credito = Decimal(str(row.total_credito))
            saldo = total_debito - total_credito

            # Solo incluir cuentas con movimiento
            if total_debito > 0 or total_credito > 0:
                resultados.append({
                    "cuenta_id": str(row.id),
                    "codigo": row.codigo,
                    "nombre": row.nombre,
                    "tipo_cuenta": row.tipo_cuenta,
                    "naturaleza": row.naturaleza,
                    "total_debito": float(total_debito),
                    "total_credito": float(total_credito),
                    "saldo": float(saldo)
                })

        return resultados
