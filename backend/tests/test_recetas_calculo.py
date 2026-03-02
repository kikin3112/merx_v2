"""
Suite de pruebas de ruptura para el módulo Recetas.

Cubre:
- Exactitud numérica del caso de prueba "Vela de Soya con Lavanda"
- Retrocompatibilidad con merma = 0
- Escala correcta de costos fijos en producción multi-lote (BUG-03b)
- Validación de bordes: merma=99.99, margen=99, CPP=0
- Precisión acumulada con muchos ingredientes
- Stock validation con merma
"""

from decimal import ROUND_HALF_UP, Decimal

import pytest

# ============================================================
# Función de cálculo aislada — no requiere DB
# (reproduce exactamente la lógica del servicio)
# ============================================================


def calcular_costo_ingrediente(cantidad: Decimal, merma: Decimal, cpp: Decimal) -> dict:
    """Reproduce la lógica de CalculadoraMargenes por ingrediente."""
    assert Decimal("0") <= merma < Decimal("100"), f"merma={merma} fuera de rango [0, 100)"
    factor = Decimal("1") - merma / Decimal("100")
    cantidad_bruta = (cantidad / factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    costo_linea = (cantidad_bruta * cpp).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"cantidad_bruta": cantidad_bruta, "costo_linea": costo_linea}


def calcular_costo_receta(ingredientes: list[dict], mano_obra: Decimal, indirectos: list[dict]) -> dict:
    """
    Reproduce CalculadoraMargenes.calcular_costo_receta().

    ingredientes: [{cantidad, merma, cpp}]
    indirectos: [{tipo: 'FIJO'|'PORCENTAJE', monto}]
    """
    costo_ingredientes = Decimal("0.00")
    for ing in ingredientes:
        r = calcular_costo_ingrediente(ing["cantidad"], ing["merma"], ing["cpp"])
        costo_ingredientes += r["costo_linea"]

    costo_base = costo_ingredientes + mano_obra

    costo_indirecto = Decimal("0.00")
    for ind in indirectos:
        if ind["tipo"] == "FIJO":
            costo_indirecto += ind["monto"]
        else:  # PORCENTAJE
            costo_indirecto += (costo_base * ind["monto"] / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    costo_total = costo_base + costo_indirecto
    return {
        "costo_ingredientes": costo_ingredientes,
        "costo_indirecto": costo_indirecto,
        "costo_total": costo_total,
    }


def calcular_produccion_multi_lote(
    ingredientes: list[dict],
    mano_obra: Decimal,
    indirectos: list[dict],
    cantidad_resultado: Decimal,
    cantidad_producir: Decimal,
) -> dict:
    """
    Reproduce producir_desde_receta() CORRECTO:
    calcula indirectos sobre base POR LOTE y escala.

    BUG anterior (ya corregido): calcular indirectos sobre base total ×N hacía
    que FIJO no escalara → costo_unitario caía al producir más lotes.
    """
    # Calcular ingredientes y MO para todos los lotes
    costo_total_ingredientes = Decimal("0.00")
    for ing in ingredientes:
        r = calcular_costo_ingrediente(ing["cantidad"], ing["merma"], ing["cpp"])
        costo_total_ingredientes += r["costo_linea"] * cantidad_producir

    costo_mano_obra_total = mano_obra * cantidad_producir

    # Costos indirectos: calcular sobre base POR LOTE y multiplicar por N
    costo_base_por_lote = (costo_total_ingredientes + costo_mano_obra_total) / cantidad_producir
    costo_indirecto_por_lote = Decimal("0.00")
    for ind in indirectos:
        if ind["tipo"] == "FIJO":
            costo_indirecto_por_lote += ind["monto"]
        else:
            costo_indirecto_por_lote += (costo_base_por_lote * ind["monto"] / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
    costo_indirecto_total = (costo_indirecto_por_lote * cantidad_producir).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )

    costo_total = costo_total_ingredientes + costo_mano_obra_total + costo_indirecto_total
    cantidad_terminada = cantidad_resultado * cantidad_producir
    costo_unitario = (costo_total / cantidad_terminada).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    resultado_1_lote = calcular_costo_receta(ingredientes, mano_obra, indirectos)
    return {
        "costo_total": costo_total,
        "costo_unitario": costo_unitario,
        "costo_unitario_1_lote": (resultado_1_lote["costo_total"] / cantidad_resultado).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        ),
    }


def calcular_produccion_multi_lote_buggy(
    ingredientes: list[dict],
    mano_obra: Decimal,
    indirectos: list[dict],
    cantidad_resultado: Decimal,
    cantidad_producir: Decimal,
) -> dict:
    """
    Reproduce el BUG original: calcular indirectos sobre base total ×N.
    Usado para demostrar que el bug hace caer el costo_unitario en multi-lote.
    """
    costo_total_ingredientes = Decimal("0.00")
    for ing in ingredientes:
        r = calcular_costo_ingrediente(ing["cantidad"], ing["merma"], ing["cpp"])
        costo_total_ingredientes += r["costo_linea"] * cantidad_producir

    costo_mano_obra_total = mano_obra * cantidad_producir
    costo_base_total = costo_total_ingredientes + costo_mano_obra_total  # BUG: base ya × N

    costo_indirecto_total = Decimal("0.00")
    for ind in indirectos:
        if ind["tipo"] == "FIJO":
            costo_indirecto_total += ind["monto"]  # BUG: no escala con N
        else:
            costo_indirecto_total += (costo_base_total * ind["monto"] / Decimal("100")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

    costo_total = costo_base_total + costo_indirecto_total
    cantidad_terminada = cantidad_resultado * cantidad_producir
    return {
        "costo_unitario": (costo_total / cantidad_terminada).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }


# ============================================================
# PRUEBA 1: Caso base del plan — "Vela de Soya con Lavanda"
# ============================================================


class TestVelaSoyaLavanda:
    INGREDIENTES = [
        {"nombre": "Cera soya", "cantidad": Decimal("200"), "merma": Decimal("5"), "cpp": Decimal("50")},
        {"nombre": "Aceite lavanda", "cantidad": Decimal("10"), "merma": Decimal("2"), "cpp": Decimal("800")},
        {"nombre": "Pabilo", "cantidad": Decimal("1"), "merma": Decimal("0"), "cpp": Decimal("500")},
        {"nombre": "Recipiente vidrio", "cantidad": Decimal("1"), "merma": Decimal("3"), "cpp": Decimal("3500")},
    ]
    MANO_OBRA = Decimal("5000")
    INDIRECTOS = [
        {"tipo": "FIJO", "monto": Decimal("1000")},
        {"tipo": "PORCENTAJE", "monto": Decimal("8")},
    ]
    MARGEN = Decimal("60")

    def test_cantidad_bruta_cera(self):
        r = calcular_costo_ingrediente(Decimal("200"), Decimal("5"), Decimal("50"))
        # 200 / 0.95 = 210.5263...
        assert r["cantidad_bruta"] == Decimal("210.5263")

    def test_costo_linea_cera(self):
        r = calcular_costo_ingrediente(Decimal("200"), Decimal("5"), Decimal("50"))
        # 210.5263 × 50 = 10526.315 → 10526.32
        assert r["costo_linea"] == Decimal("10526.32")

    def test_cantidad_bruta_lavanda(self):
        r = calcular_costo_ingrediente(Decimal("10"), Decimal("2"), Decimal("800"))
        # 10 / 0.98 = 10.2040...
        assert r["cantidad_bruta"] == Decimal("10.2041")

    def test_costo_linea_lavanda(self):
        r = calcular_costo_ingrediente(Decimal("10"), Decimal("2"), Decimal("800"))
        # 10.2041 × 800 = 8163.28
        assert r["costo_linea"] == Decimal("8163.28")

    def test_pabilo_sin_merma(self):
        r = calcular_costo_ingrediente(Decimal("1"), Decimal("0"), Decimal("500"))
        assert r["cantidad_bruta"] == Decimal("1.0000")
        assert r["costo_linea"] == Decimal("500.00")

    def test_recipiente_merma_3(self):
        r = calcular_costo_ingrediente(Decimal("1"), Decimal("3"), Decimal("3500"))
        # 1 / 0.97 = 1.0309...
        assert r["cantidad_bruta"] == Decimal("1.0309")
        # 1.0309 × 3500 = 3608.15
        assert r["costo_linea"] == Decimal("3608.15")

    def test_costo_ingredientes_total(self):
        resultado = calcular_costo_receta(self.INGREDIENTES, self.MANO_OBRA, [])
        # 10526.32 + 8163.28 + 500.00 + 3608.15 = 22797.75
        # Nota: pequeña diferencia vs plan ($22,797.84) por redondeo 4dp
        assert resultado["costo_ingredientes"] == Decimal("22797.75")

    def test_costo_total_con_indirectos(self):
        resultado = calcular_costo_receta(self.INGREDIENTES, self.MANO_OBRA, self.INDIRECTOS)
        # costo_base = 22797.75 + 5000 = 27797.75
        # PORCENTAJE: 27797.75 × 0.08 = 2223.82
        # FIJO: 1000
        # costo_indirecto = 3223.82
        # costo_total = 27797.75 + 3223.82 = 31021.57
        assert resultado["costo_total"] == Decimal("31021.57")

    def test_precio_sugerido(self):
        resultado = calcular_costo_receta(self.INGREDIENTES, self.MANO_OBRA, self.INDIRECTOS)
        costo_unitario = resultado["costo_total"]  # cantidad_resultado = 1
        precio_sugerido = (costo_unitario / (1 - self.MARGEN / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        # 31021.57 / 0.40 = 77553.925 → 77553.93
        assert precio_sugerido == Decimal("77553.93")

    def test_sin_merma_retrocompat(self):
        """Con merma=0 en todos, debe producir mismos resultados que antes."""
        ingredientes_sin_merma = [
            {"nombre": "Cera soya", "cantidad": Decimal("200"), "merma": Decimal("0"), "cpp": Decimal("50")},
            {"nombre": "Aceite lavanda", "cantidad": Decimal("10"), "merma": Decimal("0"), "cpp": Decimal("800")},
            {"nombre": "Pabilo", "cantidad": Decimal("1"), "merma": Decimal("0"), "cpp": Decimal("500")},
            {"nombre": "Recipiente vidrio", "cantidad": Decimal("1"), "merma": Decimal("0"), "cpp": Decimal("3500")},
        ]
        resultado = calcular_costo_receta(ingredientes_sin_merma, self.MANO_OBRA, [])
        # Sin merma: 200×50 + 10×800 + 1×500 + 1×3500 = 10000+8000+500+3500 = 22000
        assert resultado["costo_ingredientes"] == Decimal("22000.00")
        assert resultado["costo_total"] == Decimal("27000.00")  # + MO $5000


# ============================================================
# PRUEBA 2: Multi-lote — costo_unitario debe ser constante
# ============================================================


class TestMultiLoteConsistencia:
    INGREDIENTES = [
        {"cantidad": Decimal("200"), "merma": Decimal("5"), "cpp": Decimal("50")},
        {"cantidad": Decimal("10"), "merma": Decimal("2"), "cpp": Decimal("800")},
    ]
    MANO_OBRA = Decimal("5000")
    INDIRECTOS = [
        {"tipo": "FIJO", "monto": Decimal("1000")},
        {"tipo": "PORCENTAJE", "monto": Decimal("8")},
    ]

    def test_costo_unitario_1_lote(self):
        r = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("1"),
        )
        cu_1 = r["costo_unitario"]
        assert cu_1 == r["costo_unitario_1_lote"], "1 lote: costo_unitario debe ser igual al de 1 lote"

    def test_costo_unitario_5_lotes_igual_a_1(self):
        """El costo_unitario debe ser idéntico produciendo 1 ó 5 lotes."""
        r1 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("1"),
        )
        r5 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("5"),
        )
        assert r1["costo_unitario"] == r5["costo_unitario"], (
            f"costo_unitario inconsistente: 1 lote={r1['costo_unitario']}, " f"5 lotes={r5['costo_unitario']}"
        )

    def test_costo_unitario_100_lotes_igual_a_1(self):
        """Escala a 100 lotes."""
        r1 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("1"),
        )
        r100 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("100"),
        )
        assert (
            r1["costo_unitario"] == r100["costo_unitario"]
        ), f"costo_unitario inconsistente a escala 100: {r1['costo_unitario']} vs {r100['costo_unitario']}"

    def test_bug_fijo_no_escalaba_antes_del_fix(self):
        """
        Demuestra el bug original: con la implementación buggy, producir 5 lotes
        daba un costo_unitario MENOR que 1 lote (perverso incentivo contable).
        El fix correcto hace que FIJO escale × N lotes.
        """
        cu_buggy_1 = calcular_produccion_multi_lote_buggy(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("1"),
        )["costo_unitario"]
        cu_buggy_5 = calcular_produccion_multi_lote_buggy(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("5"),
        )["costo_unitario"]

        # El bug HACÍA que 5 lotes tuviera menor costo_unitario → demostrado
        assert cu_buggy_5 < cu_buggy_1, f"BUG no demostrado: 1_lote={cu_buggy_1}, 5_lotes={cu_buggy_5}"

        # Con el fix, son iguales
        cu_fix_1 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("1"),
        )["costo_unitario"]
        cu_fix_5 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("5"),
        )["costo_unitario"]
        assert cu_fix_1 == cu_fix_5, f"Fix fallido: {cu_fix_1} != {cu_fix_5}"

    def test_costo_total_escala_linealmente(self):
        r1 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("1"),
        )
        r5 = calcular_produccion_multi_lote(
            self.INGREDIENTES,
            self.MANO_OBRA,
            self.INDIRECTOS,
            cantidad_resultado=Decimal("1"),
            cantidad_producir=Decimal("5"),
        )
        assert r5["costo_total"] == r1["costo_total"] * 5, "costo_total debe escalar linealmente"


# ============================================================
# PRUEBA 3: Validación de bordes
# ============================================================


class TestBordes:
    def test_merma_cero(self):
        r = calcular_costo_ingrediente(Decimal("100"), Decimal("0"), Decimal("500"))
        assert r["cantidad_bruta"] == Decimal("100.0000")
        assert r["costo_linea"] == Decimal("50000.00")

    def test_merma_alta_99(self):
        """99% merma: necesita 100× la cantidad neta."""
        r = calcular_costo_ingrediente(Decimal("1"), Decimal("99"), Decimal("100"))
        # 1 / 0.01 = 100.0000
        assert r["cantidad_bruta"] == Decimal("100.0000")
        assert r["costo_linea"] == Decimal("10000.00")

    def test_merma_99_99(self):
        """99.99% merma: cantidad_bruta altísima."""
        r = calcular_costo_ingrediente(Decimal("1"), Decimal("99.99"), Decimal("1"))
        # 1 / 0.0001 = 10000
        assert r["cantidad_bruta"] == Decimal("10000.0000")

    def test_merma_igual_100_invalida(self):
        """merma = 100 debe lanzar error (división por cero)."""
        with pytest.raises(Exception):
            calcular_costo_ingrediente(Decimal("1"), Decimal("100"), Decimal("100"))

    def test_cpp_cero(self):
        """CPP = 0 (ingrediente sin inventario valorizado) — no debe romper."""
        r = calcular_costo_ingrediente(Decimal("100"), Decimal("10"), Decimal("0"))
        assert r["costo_linea"] == Decimal("0.00")

    def test_cantidad_fraccionaria_muy_pequena(self):
        """Cantidades mínimas con merma — no debe perder precisión."""
        r = calcular_costo_ingrediente(Decimal("0.0001"), Decimal("5"), Decimal("1000000"))
        # 0.0001 / 0.95 = 0.00010526... → 0.0001 (quantize 4dp)
        assert r["cantidad_bruta"] >= Decimal("0.0001")
        assert r["costo_linea"] >= Decimal("0.00")

    def test_solo_costos_fijos_sin_base(self):
        """Con costo_base = 0, PORCENTAJE da 0 pero FIJO sigue sumando."""
        resultado = calcular_costo_receta(
            [{"cantidad": Decimal("1"), "merma": Decimal("0"), "cpp": Decimal("0")}],
            Decimal("0"),
            [{"tipo": "FIJO", "monto": Decimal("500")}, {"tipo": "PORCENTAJE", "monto": Decimal("50")}],
        )
        assert resultado["costo_indirecto"] == Decimal("500.00")  # PORCENTAJE de 0 = 0

    def test_muchos_ingredientes_precision(self):
        """50 ingredientes con merma=5%, CPP=100 — la acumulación de Decimal es exacta."""
        ingredientes = [{"cantidad": Decimal("10"), "merma": Decimal("5"), "cpp": Decimal("100")}] * 50
        resultado = calcular_costo_receta(ingredientes, Decimal("0"), [])
        # Cada uno: 10/0.95 = 10.5263, × 100 = 1052.63
        # 50 × 1052.63 = 52631.50
        assert resultado["costo_ingredientes"] == Decimal("52631.50")

    def test_margen_muy_alto(self):
        """margen_objetivo = 99% → precio sugerido = costo × 100."""
        costo = Decimal("1000.00")
        margen = Decimal("99")
        precio = (costo / (1 - margen / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert precio == Decimal("100000.00")

    def test_margen_muy_bajo(self):
        """margen_objetivo = 1% → precio sugerido ≈ costo × 1.01."""
        costo = Decimal("1000.00")
        margen = Decimal("1")
        precio = (costo / (1 - margen / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert precio == Decimal("1010.10")


# ============================================================
# PRUEBA 4: Validación de stock con merma
# ============================================================


class TestStockConMerma:
    def test_stock_requerido_es_cantidad_bruta(self):
        """El stock a validar debe ser mayor que la cantidad neta cuando hay merma."""
        cantidad_neta = Decimal("100")
        merma = Decimal("20")
        factor = Decimal("1") - merma / Decimal("100")
        cantidad_bruta = (cantidad_neta / factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        # Sin merma se necesitaría 100 unidades
        # Con 20% merma se necesita 125 unidades
        assert cantidad_bruta == Decimal("125.0000")

    def test_stock_suficiente_con_merma(self):
        """Si stock = cantidad_neta, no alcanza con merma."""
        cantidad_neta = Decimal("100")
        merma = Decimal("10")
        stock = Decimal("100")  # exactamente la cantidad neta
        factor = Decimal("1") - merma / Decimal("100")
        cantidad_bruta = (cantidad_neta / factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        # Con 10% merma necesito 111.11 pero tengo 100 → insuficiente
        assert stock < cantidad_bruta

    def test_stock_suficiente_sin_merma(self):
        """Sin merma, stock = cantidad_neta es suficiente."""
        cantidad_neta = Decimal("100")
        merma = Decimal("0")
        stock = Decimal("100")
        factor = Decimal("1") - merma / Decimal("100")
        cantidad_bruta = (cantidad_neta / factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        assert stock >= cantidad_bruta


# ============================================================
# PRUEBA 5: Invariantes de negocio
# ============================================================


class TestInvariantesNegocio:
    INGREDIENTES_BASE = [
        {"cantidad": Decimal("200"), "merma": Decimal("5"), "cpp": Decimal("50")},
        {"cantidad": Decimal("10"), "merma": Decimal("2"), "cpp": Decimal("800")},
    ]
    MANO_OBRA = Decimal("5000")

    def test_merma_aumenta_costo(self):
        """Agregar merma SIEMPRE aumenta el costo (nunca lo reduce)."""
        sin_merma = calcular_costo_receta(
            [{"cantidad": Decimal("100"), "merma": Decimal("0"), "cpp": Decimal("500")}], Decimal("0"), []
        )
        con_merma = calcular_costo_receta(
            [{"cantidad": Decimal("100"), "merma": Decimal("5"), "cpp": Decimal("500")}], Decimal("0"), []
        )
        assert con_merma["costo_ingredientes"] > sin_merma["costo_ingredientes"]

    def test_mayor_merma_mayor_costo(self):
        """A mayor merma, mayor costo — relación monotónica."""
        costos = []
        for merma in [0, 5, 10, 20, 50]:
            r = calcular_costo_receta(
                [{"cantidad": Decimal("100"), "merma": Decimal(str(merma)), "cpp": Decimal("100")}], Decimal("0"), []
            )
            costos.append(r["costo_ingredientes"])
        assert costos == sorted(costos), f"Costos no son monotónicos: {costos}"

    def test_indirectos_aumentan_costo_total(self):
        """Costos indirectos activos SIEMPRE aumentan el costo_total."""
        sin_ind = calcular_costo_receta(self.INGREDIENTES_BASE, self.MANO_OBRA, [])
        con_ind = calcular_costo_receta(
            self.INGREDIENTES_BASE,
            self.MANO_OBRA,
            [{"tipo": "FIJO", "monto": Decimal("1")}, {"tipo": "PORCENTAJE", "monto": Decimal("0.01")}],
        )
        assert con_ind["costo_total"] > sin_ind["costo_total"]

    def test_precio_sugerido_mayor_que_costo(self):
        """El precio sugerido siempre debe ser mayor que el costo unitario."""
        for margen in [10, 30, 50, 60, 80]:
            costo = Decimal("30000")
            margen_d = Decimal(str(margen))
            precio = (costo / (1 - margen_d / 100)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            assert precio > costo, f"margen={margen}%: precio {precio} no es mayor que costo {costo}"

    def test_costo_total_equals_ingredientes_plus_mo_plus_indirectos(self):
        """Invariante: costo_total = costo_ingredientes + MO + indirectos."""
        resultado = calcular_costo_receta(
            self.INGREDIENTES_BASE,
            self.MANO_OBRA,
            [{"tipo": "FIJO", "monto": Decimal("1000")}, {"tipo": "PORCENTAJE", "monto": Decimal("8")}],
        )
        esperado = resultado["costo_ingredientes"] + self.MANO_OBRA + resultado["costo_indirecto"]
        assert resultado["costo_total"] == esperado

    def test_sin_ingredientes_sin_merma_costo_cero(self):
        """Receta sin ingredientes y sin MO → costo_ingredientes = 0."""
        resultado = calcular_costo_receta([], Decimal("0"), [])
        assert resultado["costo_ingredientes"] == Decimal("0.00")
        assert resultado["costo_total"] == Decimal("0.00")


# ============================================================
# PRUEBA 6: Conversión de unidades (resolver_factor_conversion)
# ============================================================

_TABLA_CONVERSION = {
    ("GRAMO", "KILOGRAMO"): Decimal("0.001"),
    ("KILOGRAMO", "GRAMO"): Decimal("1000"),
    ("MILILITRO", "LITRO"): Decimal("0.001"),
    ("LITRO", "MILILITRO"): Decimal("1000"),
    ("CENTIMETRO", "METRO"): Decimal("0.01"),
    ("METRO", "CENTIMETRO"): Decimal("100"),
}


def resolver_factor(ing_unidad: str, prod_unidad: str, custom_factor: "Decimal | None" = None) -> "Decimal | None":
    """Reproduce resolver_factor_conversion del servicio (sin DB)."""
    if ing_unidad == prod_unidad:
        return Decimal("1.000000")
    par = (ing_unidad, prod_unidad)
    if par in _TABLA_CONVERSION:
        return _TABLA_CONVERSION[par]
    return custom_factor  # simulación de equivalencia configurada


def calcular_costo_con_conversion(
    cantidad: Decimal,
    merma: Decimal,
    cpp_inventario: Decimal,
    factor: Decimal,
) -> dict:
    """Reproduce el cálculo de ingrediente con conversión de unidades."""
    merma_factor = Decimal("1") - merma / Decimal("100")
    cantidad_bruta = (cantidad / merma_factor).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    costo_efectivo = (cpp_inventario * factor).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
    costo_linea = (cantidad_bruta * costo_efectivo).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {"cantidad_bruta": cantidad_bruta, "costo_linea": costo_linea, "factor": factor}


class TestConversionUnidades:
    def test_misma_unidad_factor_1(self):
        """Misma unidad → factor siempre 1.0, sin lookup."""
        assert resolver_factor("KILOGRAMO", "KILOGRAMO") == Decimal("1.000000")
        assert resolver_factor("GRAMO", "GRAMO") == Decimal("1.000000")
        assert resolver_factor("UNIDAD", "UNIDAD") == Decimal("1.000000")

    def test_gramo_a_kilogramo_factor_0001(self):
        """GRAMO en receta, KG en inventario → factor 0.001."""
        f = resolver_factor("GRAMO", "KILOGRAMO")
        assert f == Decimal("0.001")

    def test_kilogramo_a_gramo_factor_1000(self):
        f = resolver_factor("KILOGRAMO", "GRAMO")
        assert f == Decimal("1000")

    def test_mililitro_a_litro(self):
        assert resolver_factor("MILILITRO", "LITRO") == Decimal("0.001")

    def test_par_desconocido_sin_custom_retorna_none(self):
        """Par no estándar sin equivalencia configurada → None."""
        assert resolver_factor("UNIDAD", "KILOGRAMO") is None

    def test_par_desconocido_con_custom_retorna_factor(self):
        """Par no estándar con equivalencia configurada → custom factor."""
        assert resolver_factor("UNIDAD", "KILOGRAMO", Decimal("0.5")) == Decimal("0.5")

    def test_cera_soya_vela_vaso(self):
        """
        Caso real VELA VASO:
          CERA DE SOYA: 750 GRAMO en receta, inventario en KILOGRAMO, CPP = 22600/kg
          merma = 20%
          factor = 0.001 (GRAMO → KILOGRAMO)
          cantidad_bruta = 750 / 0.80 = 937.5
          costo_efectivo = 22600 × 0.001 = 22.6
          costo_linea = 937.5 × 22.6 = 21187.50
        """
        r = calcular_costo_con_conversion(
            cantidad=Decimal("750"),
            merma=Decimal("20"),
            cpp_inventario=Decimal("22600"),
            factor=Decimal("0.001"),
        )
        assert r["cantidad_bruta"] == Decimal("937.5000")
        assert r["costo_linea"] == Decimal("21187.50")

    def test_sin_conversion_cera_soya_inflado(self):
        """
        Sin factor de conversión (factor=1), el costo se inflaría 1000×.
        750 GRAMO × 22600 = 16,950,000 (incorrecto).
        """
        r_incorrecto = calcular_costo_con_conversion(
            cantidad=Decimal("750"),
            merma=Decimal("20"),
            cpp_inventario=Decimal("22600"),
            factor=Decimal("1"),
        )
        r_correcto = calcular_costo_con_conversion(
            cantidad=Decimal("750"),
            merma=Decimal("20"),
            cpp_inventario=Decimal("22600"),
            factor=Decimal("0.001"),
        )
        assert r_incorrecto["costo_linea"] == r_correcto["costo_linea"] * 1000

    def test_estructura_profesional_costo_primo(self):
        """
        Invariante: costo_primo = material_directo + mano_obra_directa.
        """
        costo_material = Decimal("22000.00")
        costo_mo = Decimal("25000.00")
        costo_primo = costo_material + costo_mo
        assert costo_primo == Decimal("47000.00")

    def test_estructura_costo_conversion(self):
        """
        Invariante: costo_conversion = MOD + CIF.
        """
        costo_mo = Decimal("25000.00")
        cif = Decimal("50000.00")
        costo_conversion = costo_mo + cif
        assert costo_conversion == Decimal("75000.00")

    def test_lotes_posibles_stock(self):
        """
        Con stock_disponible=937.5 y cantidad_bruta_por_lote=937.5 → lotes_posibles=1.
        Con stock_disponible=1875 → lotes_posibles=2.
        """
        stock = Decimal("937.5")
        cantidad_bruta = Decimal("937.5000")
        lotes = int(stock / cantidad_bruta)
        assert lotes == 1

        stock2 = Decimal("1875")
        lotes2 = int(stock2 / cantidad_bruta)
        assert lotes2 == 2
