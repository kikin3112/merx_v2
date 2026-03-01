"""
Servicio de Análisis Costo-Volumen-Utilidad (CVU/CVP).
Núcleo de Investigación de Operaciones para el módulo Socia.
Calcula punto de equilibrio, sensibilidad, escenarios de precio y economía de escala.
"""

from decimal import ROUND_HALF_UP, Decimal
from typing import List, Optional
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from ..datos.modelos import Inventarios, Recetas, RecetasIngredientes
from ..servicios.servicio_costos_indirectos import ServicioCostosIndirectos
from ..servicios.servicio_productos import CalculadoraMargenes
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

_ZERO = Decimal("0.00")
_HUNDRED = Decimal("100")
_ONE = Decimal("1")
_D01 = Decimal("0.01")


class ServicioAnalisisCVU:
    """
    Motor de análisis IO/AO para el módulo Socia.
    Todas las operaciones usan Decimal para precisión financiera.
    """

    def __init__(self, db: Session, tenant_id: UUID):
        self.db = db
        self.tenant_id = tenant_id
        self._calculadora = CalculadoraMargenes(db=db, tenant_id=tenant_id)
        self._indirectos = ServicioCostosIndirectos(db=db, tenant_id=tenant_id)

    # ── Helpers privados ──────────────────────────────────────────────────────

    def _get_receta(self, receta_id: UUID) -> Recetas:
        receta = (
            self.db.query(Recetas)
            .options(
                joinedload(Recetas.ingredientes).joinedload(RecetasIngredientes.producto),
                joinedload(Recetas.producto_resultado),
            )
            .filter(
                Recetas.id == receta_id,
                Recetas.tenant_id == self.tenant_id,
                Recetas.deleted_at.is_(None),
            )
            .first()
        )
        if not receta:
            raise ValueError("Receta no encontrada")
        return receta

    def _calcular_cvu(self, receta_id: UUID) -> Decimal:
        """
        Costo variable unitario = (ingredientes + mano_obra + indirectos) / cantidad_resultado.
        Los costos indirectos activos del tenant se incluyen automáticamente.
        """
        receta = self._get_receta(receta_id)

        # Costo ingredientes
        product_ids = [ing.producto_id for ing in receta.ingredientes]
        inventarios_map = {}
        if product_ids:
            invs = (
                self.db.query(Inventarios)
                .filter(Inventarios.tenant_id == self.tenant_id, Inventarios.producto_id.in_(product_ids))
                .all()
            )
            inventarios_map = {inv.producto_id: inv for inv in invs}

        costo_ing = _ZERO
        for ing in receta.ingredientes:
            inv = inventarios_map.get(ing.producto_id)
            cu = inv.costo_promedio_ponderado if inv else _ZERO
            costo_ing += ing.cantidad * (cu or _ZERO)

        costo_base = costo_ing + receta.costo_mano_obra
        costo_indirecto, _ = self._indirectos.calcular_total_para_costo_base(costo_base)
        costo_total = costo_base + costo_indirecto

        if receta.cantidad_resultado <= 0:
            return _ZERO
        return (costo_total / receta.cantidad_resultado).quantize(_D01, rounding=ROUND_HALF_UP)

    def _pe(self, costos_fijos: Decimal, mc_unitario: Decimal) -> Decimal:
        """Punto de equilibrio en unidades. Retorna Decimal('Infinity') si MC=0."""
        if mc_unitario <= _ZERO:
            return Decimal("Infinity")
        return (costos_fijos / mc_unitario).quantize(_D01, rounding=ROUND_HALF_UP)

    # ── API pública ────────────────────────────────────────────────────────────

    def calcular_cvu(
        self,
        receta_id: UUID,
        precio_venta: Decimal,
        costos_fijos_periodo: Decimal,
        volumen_esperado: int,
    ) -> dict:
        """
        Análisis Costo-Volumen-Utilidad completo.

        Returns dict con:
            receta_nombre, costo_variable_unitario, margen_contribucion_unitario,
            ratio_margen_contribucion, punto_equilibrio_unidades, punto_equilibrio_ingresos,
            margen_seguridad_unidades, margen_seguridad_porcentaje, utilidad_esperada
        """
        receta = self._get_receta(receta_id)
        cvu = self._calcular_cvu(receta_id)

        mc_unitario = precio_venta - cvu
        rmc = (
            (mc_unitario / precio_venta * _HUNDRED).quantize(_D01, rounding=ROUND_HALF_UP)
            if precio_venta > 0
            else _ZERO
        )

        pe_unidades = self._pe(costos_fijos_periodo, mc_unitario)
        pe_ingresos = (
            (costos_fijos_periodo / (rmc / _HUNDRED)).quantize(_D01, rounding=ROUND_HALF_UP)
            if rmc > 0
            else Decimal("Infinity")
        )

        vol = Decimal(volumen_esperado)
        _is_inf = not pe_unidades.is_finite()
        ms_unidades = (vol - pe_unidades) if not _is_inf else Decimal("-999999.00")
        if ms_unidades.is_finite():
            ms_unidades = ms_unidades.quantize(_D01, rounding=ROUND_HALF_UP)
        ms_pct = (
            (ms_unidades / vol * _HUNDRED).quantize(_D01, rounding=ROUND_HALF_UP)
            if (vol > 0 and ms_unidades.is_finite())
            else _ZERO
        )
        utilidad = (mc_unitario * vol - costos_fijos_periodo).quantize(_D01, rounding=ROUND_HALF_UP)

        _MAX = Decimal("9999999.00")
        return {
            "receta_nombre": receta.nombre,
            "costo_variable_unitario": cvu,
            "margen_contribucion_unitario": mc_unitario.quantize(_D01, rounding=ROUND_HALF_UP),
            "ratio_margen_contribucion": rmc,
            "punto_equilibrio_unidades": pe_unidades if pe_unidades.is_finite() else _MAX,
            "punto_equilibrio_ingresos": pe_ingresos if pe_ingresos.is_finite() else _MAX,
            "margen_seguridad_unidades": ms_unidades,
            "margen_seguridad_porcentaje": ms_pct,
            "utilidad_esperada": utilidad,
        }

    def analisis_sensibilidad(
        self,
        receta_id: UUID,
        precio_venta: Decimal,
        costos_fijos: Decimal,
        volumen_base: int,
        variaciones: List[dict],
    ) -> dict:
        """
        Para cada variación, recalcula PE y utilidad.
        variaciones: [{"variable": str, "delta_porcentaje": Decimal, "ingrediente_id": Optional[str]}]
        """
        receta = self._get_receta(receta_id)
        cvu_base = self._calcular_cvu(receta_id)
        mc_base = precio_venta - cvu_base
        pe_base = self._pe(costos_fijos, mc_base)
        vol = Decimal(volumen_base)
        utilidad_base = (mc_base * vol - costos_fijos).quantize(_D01, rounding=ROUND_HALF_UP)

        resultados = []
        for v in variaciones:
            variable = v["variable"]
            delta_pct = Decimal(str(v["delta_porcentaje"]))
            factor = _ONE + delta_pct / _HUNDRED

            nuevo_precio = precio_venta
            nuevo_cvu = cvu_base
            nuevos_cf = costos_fijos
            nuevo_vol = vol

            if variable == "precio_venta":
                nuevo_precio = precio_venta * factor
            elif variable == "mano_obra":
                nuevo_cvu = cvu_base * factor  # aproximación proporcional
            elif variable == "costos_fijos":
                nuevos_cf = costos_fijos * factor
            elif variable == "volumen":
                nuevo_vol = vol * factor

            nuevo_mc = nuevo_precio - nuevo_cvu
            nuevo_pe = self._pe(nuevos_cf, nuevo_mc)
            nueva_util = (nuevo_mc * nuevo_vol - nuevos_cf).quantize(_D01, rounding=ROUND_HALF_UP)

            impacto_pe = _ZERO
            if pe_base > 0 and pe_base != Decimal("Infinity"):
                impacto_pe = ((nuevo_pe - pe_base) / pe_base * _HUNDRED).quantize(_D01, rounding=ROUND_HALF_UP)

            resultados.append(
                {
                    "variable": variable,
                    "delta_porcentaje": delta_pct,
                    "nuevo_pe_unidades": nuevo_pe,
                    "nuevo_pe_ingresos": (nuevo_pe * nuevo_precio).quantize(_D01, rounding=ROUND_HALF_UP)
                    if nuevo_pe != Decimal("Infinity")
                    else Decimal("Infinity"),
                    "nueva_utilidad": nueva_util,
                    "impacto_pe_porcentaje": impacto_pe,
                }
            )

        return {
            "receta_nombre": receta.nombre,
            "pe_base_unidades": pe_base,
            "pe_base_ingresos": (pe_base * precio_venta).quantize(_D01, rounding=ROUND_HALF_UP)
            if pe_base != Decimal("Infinity")
            else Decimal("Infinity"),
            "utilidad_base": utilidad_base,
            "resultados": resultados,
        }

    def generar_escenarios_precio(
        self,
        receta_id: UUID,
        costos_fijos: Decimal,
        volumen: int,
        precio_mercado_referencia: Optional[Decimal] = None,
    ) -> dict:
        """
        Genera 5 escenarios de precio:
        1. Precio mínimo — solo cubre costos variables (MC = 0)
        2. Precio de equilibrio — cubre CF con el volumen dado
        3. Precio objetivo — logra el margen_objetivo de la receta
        4. Precio de mercado — precio_mercado_referencia si provisto
        5. Precio premium — mercado * 1.30
        """
        receta = self._get_receta(receta_id)
        cvu = self._calcular_cvu(receta_id)
        vol = Decimal(volumen)

        def _build_escenario(nombre: str, precio: Decimal, cf: Decimal, v: Decimal) -> dict:
            if precio <= _ZERO:
                return {
                    "nombre": nombre,
                    "precio": _ZERO,
                    "margen_porcentaje": _ZERO,
                    "margen_contribucion": _ZERO,
                    "punto_equilibrio_unidades": Decimal("Infinity"),
                    "viabilidad": "NO_VIABLE",
                }

            mc = precio - cvu
            margen_pct = (mc / precio * _HUNDRED).quantize(_D01, rounding=ROUND_HALF_UP) if precio > 0 else _ZERO
            pe = self._pe(cf, mc)

            if mc <= _ZERO:
                viabilidad = "NO_VIABLE"
            elif pe <= v * Decimal("0.5"):
                viabilidad = "VIABLE"
            elif pe <= v:
                viabilidad = "CRITICO"
            else:
                viabilidad = "NO_VIABLE"

            return {
                "nombre": nombre,
                "precio": precio.quantize(_D01, rounding=ROUND_HALF_UP),
                "margen_porcentaje": margen_pct,
                "margen_contribucion": mc.quantize(_D01, rounding=ROUND_HALF_UP),
                "punto_equilibrio_unidades": pe,
                "viabilidad": viabilidad,
            }

        escenarios = []

        # 1. Precio mínimo (cubre solo CVU)
        precio_minimo = cvu
        escenarios.append(_build_escenario("Precio mínimo", precio_minimo, costos_fijos, vol))

        # 2. Precio de equilibrio (cubre CF con el volumen dado)
        # PE = CF / (P - CVU)  →  P = CVU + CF/vol
        precio_equilibrio = (cvu + costos_fijos / vol).quantize(_D01, rounding=ROUND_HALF_UP) if vol > 0 else cvu
        escenarios.append(_build_escenario("Precio de equilibrio", precio_equilibrio, costos_fijos, vol))

        # 3. Precio objetivo (margen_objetivo de la receta)
        margen_obj = getattr(receta, "margen_objetivo", None)
        if margen_obj and margen_obj > 0:
            precio_objetivo = (cvu / (_ONE - margen_obj / _HUNDRED)).quantize(_D01, rounding=ROUND_HALF_UP)
            escenarios.append(_build_escenario(f"Precio objetivo ({margen_obj}%)", precio_objetivo, costos_fijos, vol))
        else:
            # Fallback: 60% margen objetivo por defecto
            precio_objetivo = (cvu / Decimal("0.40")).quantize(_D01, rounding=ROUND_HALF_UP)
            escenarios.append(_build_escenario("Precio objetivo (60%)", precio_objetivo, costos_fijos, vol))

        # 4. Precio mercado
        if precio_mercado_referencia and precio_mercado_referencia > 0:
            escenarios.append(_build_escenario("Precio de mercado", precio_mercado_referencia, costos_fijos, vol))
        else:
            # Estimación: 2.5x CVU como referencia de mercado artesanal
            precio_mercado_est = (cvu * Decimal("2.5")).quantize(_D01, rounding=ROUND_HALF_UP)
            escenarios.append(_build_escenario("Precio mercado estimado", precio_mercado_est, costos_fijos, vol))

        # 5. Precio premium (mercado * 1.30)
        precio_ref = precio_mercado_referencia if precio_mercado_referencia else cvu * Decimal("2.5")
        precio_premium = (precio_ref * Decimal("1.30")).quantize(_D01, rounding=ROUND_HALF_UP)
        escenarios.append(_build_escenario("Precio premium", precio_premium, costos_fijos, vol))

        return {
            "receta_nombre": receta.nombre,
            "costo_variable_unitario": cvu,
            "escenarios": escenarios,
        }

    def comparar_rentabilidad(self, receta_ids: Optional[List[UUID]] = None) -> List[dict]:
        """
        Compara rentabilidad de múltiples recetas.
        Si receta_ids es None, usa todas las recetas activas del tenant.
        Ordena por margen_porcentaje descendente.
        """
        q = (
            self.db.query(Recetas)
            .options(
                joinedload(Recetas.ingredientes).joinedload(RecetasIngredientes.producto),
                joinedload(Recetas.producto_resultado),
            )
            .filter(
                Recetas.tenant_id == self.tenant_id,
                Recetas.deleted_at.is_(None),
                Recetas.estado.is_(True),
            )
        )
        if receta_ids:
            q = q.filter(Recetas.id.in_(receta_ids))

        recetas = q.all()
        resultado = []

        for receta in recetas:
            try:
                cvu = self._calcular_cvu(receta.id)
                precio_venta = _ZERO
                if receta.producto_resultado:
                    precio_venta = receta.producto_resultado.precio_venta or _ZERO

                mc = precio_venta - cvu
                margen_pct = (
                    (mc / precio_venta * _HUNDRED).quantize(_D01, rounding=ROUND_HALF_UP) if precio_venta > 0 else _ZERO
                )
                tiempo = receta.tiempo_produccion_minutos or 0
                mc_por_minuto = (mc / Decimal(tiempo)).quantize(_D01, rounding=ROUND_HALF_UP) if tiempo > 0 else None

                resultado.append(
                    {
                        "receta_id": str(receta.id),
                        "receta_nombre": receta.nombre,
                        "costo_unitario": cvu,
                        "precio_venta": precio_venta,
                        "margen_contribucion": mc.quantize(_D01, rounding=ROUND_HALF_UP),
                        "margen_porcentaje": margen_pct,
                        "tiempo_produccion_minutos": tiempo,
                        "mc_por_minuto": mc_por_minuto,
                    }
                )
            except Exception as e:
                logger.warning(f"Error calculando rentabilidad receta {receta.id}: {e}")
                continue

        return sorted(resultado, key=lambda x: x["margen_porcentaje"], reverse=True)

    def calcular_economia_escala(
        self,
        receta_id: UUID,
        costos_fijos_setup: Decimal,
        lotes: Optional[List[int]] = None,
    ) -> dict:
        """
        Calcula el costo unitario para diferentes tamaños de lote.
        El costo fijo de setup se proratea entre las unidades del lote.
        """
        if lotes is None:
            lotes = [1, 5, 10, 20, 50]

        receta = self._get_receta(receta_id)
        cvu = self._calcular_cvu(receta_id)
        costo_lote_1 = cvu + costos_fijos_setup  # setup no dividido

        escala = []
        for n_lotes in sorted(lotes):
            # Costo setup prorrateado por unidad
            unidades = Decimal(n_lotes) * receta.cantidad_resultado
            setup_unitario = (
                (costos_fijos_setup / unidades).quantize(_D01, rounding=ROUND_HALF_UP) if unidades > 0 else _ZERO
            )
            cu_lote = (cvu + setup_unitario).quantize(_D01, rounding=ROUND_HALF_UP)
            ahorro = (costo_lote_1 - cu_lote).quantize(_D01, rounding=ROUND_HALF_UP)
            escala.append(
                {
                    "lote": n_lotes,
                    "costo_unitario": cu_lote,
                    "ahorro_vs_lote_1": max(ahorro, _ZERO),
                }
            )

        return {
            "receta_nombre": receta.nombre,
            "costo_variable_unitario": cvu,
            "escala": escala,
        }
