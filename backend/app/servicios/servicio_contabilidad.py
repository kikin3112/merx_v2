"""
Servicio de Contabilidad - Lógica para asientos contables automáticos y manuales.
"""

from datetime import date
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..datos.modelos import (
    AsientosContables,
    ConfiguracionContable,
    CuentasContables,
    DetallesAsiento,
    PeriodosContables,
)
from ..utils.constantes_contables import COSTO_VENTAS, IVA_VENTAS, VENTA_CONTADO
from ..utils.logger import setup_logger
from ..utils.secuencia_helper import generar_numero_secuencia

logger = setup_logger(__name__)


class ServicioContabilidad:
    """Servicio para operaciones contables."""

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id

    def _obtener_cuenta_por_codigo(self, codigo: str) -> Optional[CuentasContables]:
        """Obtiene una cuenta contable por código."""
        return (
            self.db.query(CuentasContables)
            .filter(CuentasContables.tenant_id == self.tenant_id, CuentasContables.codigo == codigo)
            .first()
        )

    def _obtener_cuenta_configurada(self, concepto: str, lado: str = "debito") -> CuentasContables:
        """
        Busca en ConfiguracionContable por concepto y tenant_id.
        lado: "debito" o "credito" — determina qué cuenta retornar.
        Raises ValueError si no encuentra.
        """
        config = (
            self.db.query(ConfiguracionContable)
            .filter(ConfiguracionContable.tenant_id == self.tenant_id, ConfiguracionContable.concepto == concepto)
            .first()
        )

        if not config:
            raise ValueError(
                f"Configuración contable '{concepto}' no encontrada para este tenant. "
                f"Configure las cuentas en Contabilidad > Configuración."
            )

        cuenta_id = config.cuenta_debito_id if lado == "debito" else config.cuenta_credito_id
        if not cuenta_id:
            raise ValueError(f"La configuración '{concepto}' no tiene cuenta de {lado} asignada.")

        cuenta = (
            self.db.query(CuentasContables)
            .filter(CuentasContables.id == cuenta_id, CuentasContables.tenant_id == self.tenant_id)
            .first()
        )

        if not cuenta:
            raise ValueError(f"La cuenta configurada para '{concepto}' ({lado}) no existe.")

        return cuenta

    def _validar_periodo(self, fecha: date) -> UUID:
        """
        Valida que el período de la fecha esté abierto.
        Auto-crea período ABIERTO si no existe.
        Retorna periodo_id.
        """
        anio, mes = fecha.year, fecha.month

        periodo = (
            self.db.query(PeriodosContables)
            .filter(
                PeriodosContables.tenant_id == self.tenant_id,
                PeriodosContables.anio == anio,
                PeriodosContables.mes == mes,
            )
            .first()
        )

        if not periodo:
            periodo = PeriodosContables(tenant_id=self.tenant_id, anio=anio, mes=mes, estado="ABIERTO")
            self.db.add(periodo)
            self.db.flush()

        if periodo.estado == "CERRADO":
            raise ValueError(f"El período {mes}/{anio} está cerrado. No se pueden registrar movimientos.")

        return periodo.id

    def crear_asiento(
        self,
        fecha: date,
        tipo_asiento: str,
        concepto: str,
        detalles: List[dict],
        documento_referencia: Optional[str] = None,
        tercero_id: Optional[UUID] = None,
    ) -> AsientosContables:
        """
        Crea un asiento contable validando que esté balanceado.

        Args:
            fecha: Fecha del asiento
            tipo_asiento: VENTAS, COMPRAS, PRODUCCION, AJUSTE, etc.
            concepto: Descripción del asiento
            detalles: Lista de dicts con {cuenta_id, debito, credito, descripcion}
            documento_referencia: Número de documento origen
            tercero_id: UUID del tercero asociado

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
            raise ValueError(f"Asiento desbalanceado: Débitos={total_debito}, Créditos={total_credito}")

        if total_debito == 0:
            raise ValueError("El asiento no puede tener todos los valores en cero")

        # Validar período contable
        periodo_id = self._validar_periodo(fecha)

        # Generar número
        numero = generar_numero_secuencia(self.db, "ASIENTOS", self.tenant_id)

        asiento = AsientosContables(
            tenant_id=self.tenant_id,
            numero_asiento=numero,
            fecha=fecha,
            tipo_asiento=tipo_asiento,
            concepto=concepto,
            documento_referencia=documento_referencia,
            estado="ACTIVO",
            periodo_id=periodo_id,
            tercero_id=tercero_id,
        )
        self.db.add(asiento)
        self.db.flush()

        for det in detalles:
            # Validar que la cuenta existe
            cuenta = (
                self.db.query(CuentasContables)
                .filter(CuentasContables.id == det["cuenta_id"], CuentasContables.tenant_id == self.tenant_id)
                .first()
            )
            if not cuenta:
                raise ValueError(f"Cuenta contable {det['cuenta_id']} no encontrada")

            detalle = DetallesAsiento(
                tenant_id=self.tenant_id,
                asiento_id=asiento.id,
                cuenta_id=det["cuenta_id"],
                debito=Decimal(str(det.get("debito", 0))),
                credito=Decimal(str(det.get("credito", 0))),
                descripcion=det.get("descripcion", ""),
            )
            self.db.add(detalle)

        self.db.flush()

        logger.info(f"Asiento {numero} creado - Tipo: {tipo_asiento}, Total: {total_debito}")

        return asiento

    def crear_asiento_venta(
        self,
        fecha: date,
        subtotal: Decimal,
        total_iva: Decimal,
        total: Decimal,
        documento_referencia: str,
        tercero_id: Optional[UUID] = None,
        cogs: Optional[Decimal] = None,
    ) -> AsientosContables:
        """
        Crea asiento contable automático para una venta/factura.
        Usa cuentas de ConfiguracionContable (concepto VENTA_CONTADO e IVA_VENTAS).

        DEBE: Cuenta configurada VENTA_CONTADO.debito (ej: 1105 Caja)
        HABER: Cuenta configurada VENTA_CONTADO.credito (ej: 4135 Ventas)
        HABER: Cuenta configurada IVA_VENTAS.credito (ej: 2408 IVA) -- si hay IVA

        Si se proporciona cogs (Costo de Ventas calculado antes del movimiento):
        DEBE: Cuenta COSTO_VENTAS.debito (ej: 6135 Costo de mercancía vendida)
        HABER: Cuenta COSTO_VENTAS.credito (ej: 1435 Inventario) — E8 fix (NIIF 15)
        """
        cuenta_caja = self._obtener_cuenta_configurada(VENTA_CONTADO, "debito")
        cuenta_ventas = self._obtener_cuenta_configurada(VENTA_CONTADO, "credito")

        # Ingresos netos = total - IVA (garantiza balance con descuentos globales/línea)
        ingresos_netos = total - total_iva

        detalles = [
            {
                "cuenta_id": cuenta_caja.id,
                "debito": total,
                "credito": Decimal("0"),
                "descripcion": f"Cobro venta {documento_referencia}",
            },
            {
                "cuenta_id": cuenta_ventas.id,
                "debito": Decimal("0"),
                "credito": ingresos_netos,
                "descripcion": f"Venta {documento_referencia}",
            },
        ]

        if total_iva > 0:
            cuenta_iva = self._obtener_cuenta_configurada(IVA_VENTAS, "credito")
            detalles.append(
                {
                    "cuenta_id": cuenta_iva.id,
                    "debito": Decimal("0"),
                    "credito": total_iva,
                    "descripcion": f"IVA venta {documento_referencia}",
                }
            )

        if cogs and cogs > 0:
            try:
                cuenta_costo = self._obtener_cuenta_configurada(COSTO_VENTAS, "debito")
                cuenta_inventario = self._obtener_cuenta_configurada(COSTO_VENTAS, "credito")
                detalles.append(
                    {
                        "cuenta_id": cuenta_costo.id,
                        "debito": cogs,
                        "credito": Decimal("0"),
                        "descripcion": f"Costo de ventas {documento_referencia}",
                    }
                )
                detalles.append(
                    {
                        "cuenta_id": cuenta_inventario.id,
                        "debito": Decimal("0"),
                        "credito": cogs,
                        "descripcion": f"Salida inventario {documento_referencia}",
                    }
                )
            except ValueError:
                logger.warning(
                    f"Configuración COSTO_VENTAS no encontrada — asiento sin COGS para {documento_referencia}"
                )

        return self.crear_asiento(
            fecha=fecha,
            tipo_asiento="VENTAS",
            concepto=f"Venta según {documento_referencia}",
            detalles=detalles,
            documento_referencia=documento_referencia,
            tercero_id=tercero_id,
        )

    def crear_asiento_anulacion_venta(
        self,
        fecha: date,
        subtotal: Decimal,
        total_iva: Decimal,
        total: Decimal,
        documento_referencia: str,
        tercero_id: Optional[UUID] = None,
        cogs: Optional[Decimal] = None,
    ) -> AsientosContables:
        """
        Crea asiento contable de reversión para anulación de venta.
        Invierte el asiento original usando cuentas de ConfiguracionContable.
        Si se proporciona cogs, revierte también el asiento COGS.
        """
        cuenta_caja = self._obtener_cuenta_configurada(VENTA_CONTADO, "debito")
        cuenta_ventas = self._obtener_cuenta_configurada(VENTA_CONTADO, "credito")

        # Ingresos netos = total - IVA (garantiza balance con descuentos globales/línea)
        ingresos_netos = total - total_iva

        detalles = [
            {
                "cuenta_id": cuenta_caja.id,
                "debito": Decimal("0"),
                "credito": total,
                "descripcion": f"Anulación venta {documento_referencia}",
            },
            {
                "cuenta_id": cuenta_ventas.id,
                "debito": ingresos_netos,
                "credito": Decimal("0"),
                "descripcion": f"Anulación venta {documento_referencia}",
            },
        ]

        if total_iva > 0:
            cuenta_iva = self._obtener_cuenta_configurada(IVA_VENTAS, "credito")
            detalles.append(
                {
                    "cuenta_id": cuenta_iva.id,
                    "debito": total_iva,
                    "credito": Decimal("0"),
                    "descripcion": f"Anulación IVA venta {documento_referencia}",
                }
            )

        if cogs and cogs > 0:
            try:
                cuenta_costo = self._obtener_cuenta_configurada(COSTO_VENTAS, "debito")
                cuenta_inventario = self._obtener_cuenta_configurada(COSTO_VENTAS, "credito")
                detalles.append(
                    {
                        "cuenta_id": cuenta_costo.id,
                        "debito": Decimal("0"),
                        "credito": cogs,
                        "descripcion": f"Anulación costo de ventas {documento_referencia}",
                    }
                )
                detalles.append(
                    {
                        "cuenta_id": cuenta_inventario.id,
                        "debito": cogs,
                        "credito": Decimal("0"),
                        "descripcion": f"Reingreso inventario {documento_referencia}",
                    }
                )
            except ValueError:
                logger.warning(
                    f"Configuración COSTO_VENTAS no encontrada — anulación sin reversión COGS para {documento_referencia}"
                )

        return self.crear_asiento(
            fecha=fecha,
            tipo_asiento="VENTAS",
            concepto=f"Anulación venta {documento_referencia}",
            detalles=detalles,
            documento_referencia=f"ANUL-{documento_referencia}",
            tercero_id=tercero_id,
        )

    def obtener_balance_prueba(
        self, fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None
    ) -> List[dict]:
        """
        Genera balance de prueba: para cada cuenta, suma débitos y créditos.
        """
        query = (
            self.db.query(
                CuentasContables.id,
                CuentasContables.codigo,
                CuentasContables.nombre,
                CuentasContables.tipo_cuenta,
                CuentasContables.naturaleza,
                func.coalesce(func.sum(DetallesAsiento.debito), 0).label("total_debito"),
                func.coalesce(func.sum(DetallesAsiento.credito), 0).label("total_credito"),
            )
            .outerjoin(
                DetallesAsiento,
                (DetallesAsiento.cuenta_id == CuentasContables.id) & (DetallesAsiento.tenant_id == self.tenant_id),
            )
            .outerjoin(
                AsientosContables,
                (AsientosContables.id == DetallesAsiento.asiento_id) & (AsientosContables.estado == "ACTIVO"),
            )
            .filter(CuentasContables.tenant_id == self.tenant_id, CuentasContables.acepta_movimiento)
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
            CuentasContables.naturaleza,
        ).order_by(CuentasContables.codigo)

        resultados = []
        for row in query.all():
            total_debito = Decimal(str(row.total_debito))
            total_credito = Decimal(str(row.total_credito))
            saldo = total_debito - total_credito

            # Solo incluir cuentas con movimiento
            if total_debito > 0 or total_credito > 0:
                resultados.append(
                    {
                        "cuenta_id": str(row.id),
                        "codigo": row.codigo,
                        "nombre": row.nombre,
                        "tipo_cuenta": row.tipo_cuenta,
                        "naturaleza": row.naturaleza,
                        "total_debito": str(total_debito),
                        "total_credito": str(total_credito),
                        "saldo": str(saldo),
                    }
                )

        return resultados
