"""
Tests para ServicioPDF — WCAG helper, branding de colores, logo S3.
"""

from unittest.mock import patch

# ---------------------------------------------------------------------------
# Task 1 — WCAG helper tests
# ---------------------------------------------------------------------------


def test_wcag_text_color_dark_bg():
    """Color oscuro (#1a1a2e) → texto blanco para legibilidad WCAG."""
    from app.servicios.servicio_pdf import _wcag_text_color

    assert _wcag_text_color("#1a1a2e") == "#FFFFFF"


def test_wcag_text_color_light_bg():
    """Color claro (#FFFFFF) → texto oscuro para legibilidad WCAG."""
    from app.servicios.servicio_pdf import _wcag_text_color

    assert _wcag_text_color("#FFFFFF") == "#1a1a2e"


def test_wcag_text_color_primary_default():
    """Azul estándar (#1976D2) → texto blanco (luminance < 0.5)."""
    from app.servicios.servicio_pdf import _wcag_text_color

    assert _wcag_text_color("#1976D2") == "#FFFFFF"


def test_wcag_text_color_coral():
    """Coral Carbon Vivo (#FF9B65) es claro → texto oscuro."""
    from app.servicios.servicio_pdf import _wcag_text_color

    assert _wcag_text_color("#FF9B65") == "#1a1a2e"


# ---------------------------------------------------------------------------
# Task 2 — Branded PDF generation tests
# ---------------------------------------------------------------------------

_MINIMAL_TENANT = {
    "nombre": "Test SA",
    "nit": "900123456",
    "email_contacto": "test@test.com",
    "telefono": "3001234567",
    "direccion": "Calle 1 # 2-3",
    "ciudad": "Bogota",
    "departamento": "Cundinamarca",
    "url_logo": None,
}

_MINIMAL_CLIENTE = {
    "nombre": "Cliente Test",
    "tipo_documento": "CC",
    "numero_documento": "12345678",
    "direccion": None,
    "telefono": None,
    "email": None,
}

_MINIMAL_DETALLE = [
    {
        "producto_nombre": "Producto A",
        "cantidad": 2,
        "precio_unitario": 10000,
        "descuento": 0,
        "porcentaje_iva": 19,
    }
]


def test_pdf_branded_usa_color_tenant():
    """generar_factura_pdf() produce bytes PDF válidos con color_primario personalizado."""
    from app.servicios.servicio_pdf import ServicioPDF

    tenant = {**_MINIMAL_TENANT, "color_primario": "#FF0000", "color_secundario": "#000000"}
    servicio = ServicioPDF(tenant)
    pdf_bytes = servicio.generar_factura_pdf(
        numero="F-001",
        fecha="2026-01-01",
        cliente=_MINIMAL_CLIENTE,
        detalles=_MINIMAL_DETALLE,
        subtotal=20000,
        descuento=0,
        base_gravable=20000,
        total_iva=3800,
        total=23800,
    )
    assert pdf_bytes[:4] == b"%PDF", "El PDF debe comenzar con la firma %PDF"
    assert len(pdf_bytes) > 1000, "El PDF debe tener contenido sustancial"


def test_pdf_cotizacion_usa_color_tenant():
    """generar_cotizacion_pdf() produce bytes PDF válidos con color_primario personalizado."""
    from app.servicios.servicio_pdf import ServicioPDF

    tenant = {**_MINIMAL_TENANT, "color_primario": "#003366", "color_secundario": "#666666"}
    servicio = ServicioPDF(tenant)
    pdf_bytes = servicio.generar_cotizacion_pdf(
        numero="C-001",
        fecha="2026-01-01",
        fecha_vencimiento="2026-01-31",
        cliente=_MINIMAL_CLIENTE,
        detalles=_MINIMAL_DETALLE,
        subtotal=20000,
        descuento=0,
        base_gravable=20000,
        total_iva=3800,
        total=23800,
    )
    assert pdf_bytes[:4] == b"%PDF", "El PDF debe comenzar con la firma %PDF"
    assert len(pdf_bytes) > 1000, "El PDF debe tener contenido sustancial"


def test_pdf_logo_s3_key_detectado():
    """Cuando url_logo es una S3 key, se llama a ServicioAlmacenamiento.obtener_imagen_bytes()."""
    from app.servicios.servicio_pdf import ServicioPDF

    tenant = {
        **_MINIMAL_TENANT,
        "url_logo": "tenants/abc/logo.png",  # S3 key — no comienza con "data:" ni "/"
        "color_primario": "#1976D2",
        "color_secundario": "#424242",
    }

    # PNG válido 10x10 rojo — generado con PIL Image.new('RGB', (10, 10), (255, 0, 0))
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x02"
        b"\x00\x00\x00\x02PX\xea\x00\x00\x00\x12IDATx\x9cc\xfc\xcf\x80\x0f0\xe1"
        b"\x95\x1d\xb1\xd2\x00A,\x01\x13\xb1\ns\x13\x00\x00\x00\x00IEND\xaeB`\x82"
    )

    with patch(
        "app.servicios.servicio_almacenamiento.ServicioAlmacenamiento.obtener_imagen_bytes",
        return_value=png_bytes,
    ) as mock_obtener:
        servicio = ServicioPDF(tenant)
        # generar_factura_pdf llama internamente _build_header que detecta la S3 key
        servicio.generar_factura_pdf(
            numero="F-002",
            fecha="2026-01-01",
            cliente=_MINIMAL_CLIENTE,
            detalles=_MINIMAL_DETALLE,
            subtotal=20000,
            descuento=0,
            base_gravable=20000,
            total_iva=3800,
            total=23800,
        )
        mock_obtener.assert_called_once_with("tenants/abc/logo.png")
