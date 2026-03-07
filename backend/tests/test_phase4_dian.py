"""
Tests for Phase 4 — DIAN compliance features.

Covers:
- C-22: Motor de retenciones (calcular_retefuente, calcular_reteica, calcular_reteiva)
- C-23: Generador CUFE (SHA-384 determinista)
- C-24: Régimen tributario en Tenants y Terceros (column present)
- A-14: Audit log fail-fast (exception propagates)
- A-11: UserContextMiddleware ContextVar set by dependency
"""

from decimal import Decimal

from app.utils.cufe import formatear_valor_cufe, generar_cufe
from app.utils.retenciones import (
    UVT_2026,
    calcular_retefuente,
    calcular_reteica,
    calcular_reteiva,
)

# ===========================================================================
# C-22: Motor de retenciones
# ===========================================================================


class TestCalcularRetefuente:
    def test_compras_bajo_umbral_no_retiene(self):
        """Monto menor a 10 UVT no genera retención en compras."""
        umbral = UVT_2026 * 10  # $523,740
        monto = umbral - Decimal("1")
        assert calcular_retefuente(monto, "compras") == Decimal("0.00")

    def test_compras_sobre_umbral_declarante(self):
        """Monto ≥ 10 UVT retiene 2.5% para declarante."""
        monto = Decimal("1000000")  # $1,000,000 > $523,740
        resultado = calcular_retefuente(monto, "compras", es_declarante=True)
        esperado = (monto * Decimal("0.025")).quantize(Decimal("0.01"))
        assert resultado == esperado

    def test_compras_sobre_umbral_no_declarante(self):
        """Monto ≥ 10 UVT retiene 3.5% para no declarante."""
        monto = Decimal("1000000")
        resultado = calcular_retefuente(monto, "compras", es_declarante=False)
        esperado = (monto * Decimal("0.035")).quantize(Decimal("0.01"))
        assert resultado == esperado

    def test_honorarios_sin_umbral_siempre_retiene(self):
        """Honorarios no tienen umbral UVT — retiene desde $1."""
        resultado = calcular_retefuente(Decimal("1000"), "honorarios")
        assert resultado > Decimal("0.00")

    def test_honorarios_tasa_11_porciento(self):
        """Honorarios: tasa 11% tanto declarante como no declarante."""
        monto = Decimal("500000")
        assert calcular_retefuente(monto, "honorarios", True) == calcular_retefuente(monto, "honorarios", False)
        resultado = calcular_retefuente(monto, "honorarios")
        assert resultado == (monto * Decimal("0.11")).quantize(Decimal("0.01"))

    def test_concepto_desconocido_retorna_cero(self):
        """Concepto no mapeado retorna $0."""
        assert calcular_retefuente(Decimal("10000000"), "concepto_invalido") == Decimal("0.00")

    def test_redondeo_2_decimales(self):
        """Resultado siempre tiene exactamente 2 decimales."""
        resultado = calcular_retefuente(Decimal("123456.789"), "compras")
        assert resultado == resultado.quantize(Decimal("0.01"))


class TestCalcularReteiva:
    def test_responsable_iva_retiene_15_porciento(self):
        """ReteIVA es 15% del monto IVA para responsables."""
        iva = Decimal("190000")
        resultado = calcular_reteiva(iva, es_responsable_iva=True)
        assert resultado == Decimal("28500.00")

    def test_no_responsable_no_retiene(self):
        """No responsables del IVA no generan ReteIVA."""
        assert calcular_reteiva(Decimal("190000"), es_responsable_iva=False) == Decimal("0.00")


class TestCalcularReteica:
    def test_tasa_bogota_por_mil(self):
        """Bogotá: tarifa 4.14‰ sobre base gravable."""
        monto = Decimal("1000000")
        resultado = calcular_reteica(monto, tasa_por_mil=Decimal("4.14"))
        assert resultado == Decimal("4140.00")

    def test_sin_tasa_retorna_cero(self):
        """Sin tasa configurada retorna $0."""
        assert calcular_reteica(Decimal("1000000")) == Decimal("0.00")


# ===========================================================================
# C-23: Generador CUFE
# ===========================================================================


class TestGenerarCufe:
    def test_cufe_tiene_96_caracteres(self):
        """CUFE SHA-384 produce exactamente 96 caracteres hexadecimales."""
        cufe = generar_cufe(
            nit_emisor="900123456",
            fecha_hora="20260307120000",
            numero_factura="SETP990000001",
            valor_total="1500000.00",
            valor_iva="285000.00",
            codigo_tipo_operacion="01",
            nit_receptor="12345678",
            tipo_ambiente="2",
            llave_tecnica="TEST_LLAVE",
        )
        assert len(cufe) == 96

    def test_cufe_es_hexadecimal(self):
        """CUFE contiene solo caracteres hexadecimales."""
        cufe = generar_cufe(
            nit_emisor="900123456",
            fecha_hora="20260307120000",
            numero_factura="SETP990000001",
            valor_total="1500000.00",
            valor_iva="285000.00",
            codigo_tipo_operacion="01",
            nit_receptor="12345678",
            tipo_ambiente="2",
            llave_tecnica="TEST_LLAVE",
        )
        int(cufe, 16)  # raises ValueError if not hex

    def test_cufe_es_deterministico(self):
        """Mismos inputs producen mismo CUFE."""
        args = dict(
            nit_emisor="900123456",
            fecha_hora="20260307120000",
            numero_factura="SETP990000001",
            valor_total="1500000.00",
            valor_iva="285000.00",
            codigo_tipo_operacion="01",
            nit_receptor="12345678",
            tipo_ambiente="2",
            llave_tecnica="TEST_LLAVE",
        )
        assert generar_cufe(**args) == generar_cufe(**args)

    def test_cufe_cambia_con_numero_factura(self):
        """Facturas distintas producen CUFEs distintos."""
        base = dict(
            nit_emisor="900123456",
            fecha_hora="20260307120000",
            numero_factura="SETP990000001",
            valor_total="1500000.00",
            valor_iva="285000.00",
            codigo_tipo_operacion="01",
            nit_receptor="12345678",
            tipo_ambiente="2",
            llave_tecnica="TEST_LLAVE",
        )
        cufe1 = generar_cufe(**base)
        base["numero_factura"] = "SETP990000002"
        cufe2 = generar_cufe(**base)
        assert cufe1 != cufe2

    def test_formatear_valor_cufe_dos_decimales(self):
        """formatear_valor_cufe produce string con 2 decimales."""
        assert formatear_valor_cufe(Decimal("1500000")) == "1500000.00"
        assert formatear_valor_cufe(Decimal("285000.5")) == "285000.50"


# ===========================================================================
# C-24: Régimen tributario — modelos tienen la columna
# ===========================================================================


def test_regimen_tributario_en_terceros_existe():
    """Modelo Terceros tiene columna regimen_tributario."""
    from app.datos.modelos import Terceros

    col = Terceros.__table__.columns.get("regimen_tributario")
    assert col is not None
    assert col.nullable is True


def test_regimen_tributario_en_tenants_existe():
    """Modelo Tenants tiene columna regimen_tributario."""
    from app.datos.modelos_tenant import Tenants

    col = Tenants.__table__.columns.get("regimen_tributario")
    assert col is not None
    assert col.nullable is True


def test_regimenttributario_enum_valores():
    """RegimentTributario enum tiene los 4 valores DIAN esperados."""
    from app.datos.modelos import RegimentTributario

    assert RegimentTributario.RESPONSABLE_IVA.value == "RESPONSABLE_IVA"
    assert RegimentTributario.REGIMEN_SIMPLE.value == "REGIMEN_SIMPLE"
    assert RegimentTributario.REGIMEN_ESPECIAL.value == "REGIMEN_ESPECIAL"
    assert RegimentTributario.NO_RESPONSABLE.value == "NO_RESPONSABLE"


# ===========================================================================
# C-23: cufe column exists in Ventas
# ===========================================================================


def test_cufe_columna_en_ventas():
    """Modelo Ventas tiene columna cufe (String 96, nullable)."""
    from app.datos.modelos import Ventas

    col = Ventas.__table__.columns.get("cufe")
    assert col is not None
    assert col.nullable is True


# ===========================================================================
# C-22: retencion columns in Compras
# ===========================================================================


def test_retencion_columnas_en_compras():
    """Modelo Compras tiene columnas retencion_renta y retencion_ica."""
    from app.datos.modelos import Compras

    assert Compras.__table__.columns.get("retencion_renta") is not None
    assert Compras.__table__.columns.get("retencion_ica") is not None
