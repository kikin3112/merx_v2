"""
Servicio de generación de PDFs para facturas y cotizaciones.
Utiliza ReportLab para generar PDFs profesionales.
"""

import base64
import io
import os
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.platypus import Image as RLImage


def _wcag_text_color(hex_color: str) -> str:
    """Returns #FFFFFF or #1a1a2e based on WCAG relative luminance.

    Uses simplified formula: luminance = (0.299R + 0.587G + 0.114B) / 255
    Threshold 0.5 gives readable contrast for both directions.
    """
    c = hex_color.lstrip("#")
    if len(c) != 6:
        return "#FFFFFF"  # fallback for invalid hex
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#FFFFFF" if luminance < 0.5 else "#1a1a2e"


def _formato_moneda(valor) -> str:
    """Formatea un valor numérico como pesos colombianos."""
    try:
        v = float(valor)
    except (TypeError, ValueError):
        v = 0.0
    if v < 0:
        return f"-${abs(v):,.0f}".replace(",", ".")
    return f"${v:,.0f}".replace(",", ".")


def _crear_estilos():
    """Crea los estilos de párrafo personalizados."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            name="DocTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#1a1a2e"),
            spaceAfter=2 * mm,
            alignment=TA_CENTER,
        )
    )

    styles.add(
        ParagraphStyle(
            name="DocSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            alignment=TA_CENTER,
            spaceAfter=4 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=11,
            textColor=colors.HexColor("#1a1a2e"),
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InfoText",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#333333"),
            leading=13,
        )
    )

    styles.add(
        ParagraphStyle(
            name="InfoTextRight",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#333333"),
            alignment=TA_RIGHT,
            leading=13,
        )
    )

    styles.add(
        ParagraphStyle(
            name="FooterText",
            parent=styles["Normal"],
            fontSize=8,
            textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER,
            spaceBefore=6 * mm,
        )
    )

    return styles


class ServicioPDF:
    """Genera PDFs profesionales para documentos comerciales."""

    def __init__(self, tenant_info: dict):
        """
        Args:
            tenant_info: Dict con info del tenant:
                - nombre, nit, email_contacto, telefono, direccion, ciudad, departamento
                - color_primario: hex string (e.g. "#1976D2") — optional, defaults to #1976D2
                - color_secundario: hex string — optional, defaults to #424242
        """
        self.tenant = tenant_info
        self.primary_color = tenant_info.get("color_primario") or "#1976D2"
        self.secondary_color = tenant_info.get("color_secundario") or "#424242"
        self.text_on_primary = _wcag_text_color(self.primary_color)
        self.styles = _crear_estilos()

    def _build_header(self, titulo: str, numero: str, fecha: str, fecha_vencimiento: Optional[str] = None) -> list:
        """Construye el header del documento."""
        elements = []

        # Logo del tenant (si existe)
        url_logo = self.tenant.get("url_logo")
        if url_logo:
            try:
                if url_logo.startswith("data:"):
                    # base64 data URL: "data:image/png;base64,iVBOR..."
                    _hdr, b64data = url_logo.split(",", 1)
                    img_bytes = base64.b64decode(b64data)
                    logo_img = RLImage(io.BytesIO(img_bytes), width=2 * cm, height=2 * cm)
                elif url_logo.startswith("/"):
                    # legacy: filesystem path
                    static_base = os.path.join(os.path.dirname(__file__), "..", "..", "static")
                    logo_path = os.path.normpath(os.path.join(static_base, url_logo.replace("/static/", "", 1)))
                    if not os.path.exists(logo_path):
                        raise FileNotFoundError(f"Logo not found: {logo_path}")
                    logo_img = RLImage(logo_path, width=2 * cm, height=2 * cm)
                else:
                    # New: S3 key path (e.g. "tenants/uuid/logo.png")
                    from app.servicios.servicio_almacenamiento import ServicioAlmacenamiento

                    storage = ServicioAlmacenamiento()
                    img_bytes = storage.obtener_imagen_bytes(url_logo)
                    if img_bytes is None:
                        raise ValueError("S3 logo not found")
                    logo_img = RLImage(io.BytesIO(img_bytes), width=3 * cm, height=3 * cm)
                logo_img.hAlign = "CENTER"
                elements.append(logo_img)
                elements.append(Spacer(1, 0.3 * cm))
            except Exception:
                pass

        # Nombre empresa
        elements.append(Paragraph(self.tenant.get("nombre", "Empresa"), self.styles["DocTitle"]))

        # Info empresa
        info_parts = []
        if self.tenant.get("nit"):
            info_parts.append(f"NIT: {self.tenant['nit']}")
        if self.tenant.get("direccion"):
            info_parts.append(self.tenant["direccion"])
        if self.tenant.get("ciudad"):
            loc = self.tenant["ciudad"]
            if self.tenant.get("departamento"):
                loc += f", {self.tenant['departamento']}"
            info_parts.append(loc)
        if self.tenant.get("telefono"):
            info_parts.append(f"Tel: {self.tenant['telefono']}")
        if self.tenant.get("email_contacto"):
            info_parts.append(self.tenant["email_contacto"])

        if info_parts:
            elements.append(Paragraph(" | ".join(info_parts), self.styles["DocSubtitle"]))

        elements.append(
            HRFlowable(width="100%", thickness=1, color=colors.HexColor(self.primary_color), spaceAfter=4 * mm)
        )

        # Titulo documento + numero + fecha
        doc_info = [
            [
                Paragraph(f"<b>{titulo}</b>", self.styles["SectionTitle"]),
                Paragraph(
                    f"<b>No:</b> {numero}<br/>"
                    f"<b>Fecha:</b> {fecha}" + (f"<br/><b>Vence:</b> {fecha_vencimiento}" if fecha_vencimiento else ""),
                    self.styles["InfoTextRight"],
                ),
            ]
        ]
        doc_table = Table(doc_info, colWidths=["60%", "40%"])
        doc_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ]
            )
        )
        elements.append(doc_table)
        elements.append(Spacer(1, 3 * mm))

        return elements

    def _build_cliente_info(self, cliente: dict) -> list:
        """Construye la sección de información del cliente."""
        elements = []

        elements.append(Paragraph("CLIENTE", self.styles["SectionTitle"]))

        info_parts = [f"<b>{cliente.get('nombre', 'N/A')}</b>"]
        if cliente.get("numero_documento"):
            tipo = cliente.get("tipo_documento", "")
            info_parts.append(f"{tipo}: {cliente['numero_documento']}")
        if cliente.get("direccion"):
            info_parts.append(cliente["direccion"])
        if cliente.get("telefono"):
            info_parts.append(f"Tel: {cliente['telefono']}")
        if cliente.get("email"):
            info_parts.append(cliente["email"])

        elements.append(Paragraph("<br/>".join(info_parts), self.styles["InfoText"]))
        elements.append(Spacer(1, 4 * mm))

        return elements

    def _build_tabla_detalles(self, detalles: list) -> list:
        """Construye la tabla de detalles del documento."""
        elements = []

        # Header de tabla
        header = ["#", "Producto", "Cant.", "P. Unit.", "Desc.", "IVA %", "Total"]
        data = [header]

        for i, det in enumerate(detalles, 1):
            cantidad = float(det.get("cantidad", 0))
            precio = float(det.get("precio_unitario", 0))
            descuento_pct = float(det.get("descuento", 0))
            iva_pct = float(det.get("porcentaje_iva", 0))
            subtotal = cantidad * precio
            descuento_monto = subtotal * descuento_pct / 100
            base = subtotal - descuento_monto
            iva_val = base * (iva_pct / 100)
            total = base + iva_val

            data.append(
                [
                    str(i),
                    det.get("producto_nombre", det.get("descripcion", "Producto")),
                    f"{cantidad:g}",
                    _formato_moneda(precio),
                    f"{descuento_pct:g}%" if descuento_pct > 0 else "-",
                    f"{iva_pct:g}%" if iva_pct > 0 else "-",
                    _formato_moneda(total),
                ]
            )

        col_widths = [25, 180, 40, 70, 55, 45, 70]
        table = Table(data, colWidths=col_widths)

        style = TableStyle(
            [
                # Header
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(self.primary_color)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor(self.text_on_primary)),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("TOPPADDING", (0, 0), (-1, 0), 6),
                # Body
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
                ("TOPPADDING", (0, 1), (-1, -1), 4),
                ("ALIGN", (0, 1), (0, -1), "CENTER"),  # #
                ("ALIGN", (2, 1), (2, -1), "CENTER"),  # Cant
                ("ALIGN", (3, 1), (-1, -1), "RIGHT"),  # Prices
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
                ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor(self.primary_color)),
            ]
        )

        # Zebra striping
        for i in range(1, len(data)):
            if i % 2 == 0:
                style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#f8f9fa"))

        table.setStyle(style)
        elements.append(table)

        return elements

    def _build_totales(self, subtotal, descuento, base_gravable, total_iva, total, descuento_global_pct=None) -> list:
        """Construye el bloque de totales."""
        elements = []
        elements.append(Spacer(1, 4 * mm))

        totales_data = []
        totales_data.append(["Subtotal:", _formato_moneda(subtotal)])
        if float(descuento) > 0:
            totales_data.append(["Descuento:", f"-{_formato_moneda(descuento)}"])
        if descuento_global_pct and float(descuento_global_pct) > 0:
            totales_data.append([f"Descuento Global ({float(descuento_global_pct):g}%):", "Incluido"])
        totales_data.append(["Base Gravable:", _formato_moneda(base_gravable)])
        if float(total_iva) > 0:
            totales_data.append(["IVA:", _formato_moneda(total_iva)])
        totales_data.append(["TOTAL:", _formato_moneda(total)])

        totales_table = Table(totales_data, colWidths=[370, 115])
        style = TableStyle(
            [
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (0, -1), "RIGHT"),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                # Total row bold
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, -1), (-1, -1), 11),
                ("LINEABOVE", (0, -1), (-1, -1), 1, colors.HexColor(self.primary_color)),
                ("TOPPADDING", (0, -1), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
        totales_table.setStyle(style)
        elements.append(totales_table)

        return elements

    def _build_footer(self, observaciones: Optional[str] = None) -> list:
        """Construye el footer del documento."""
        elements = []

        if observaciones:
            elements.append(Spacer(1, 4 * mm))
            elements.append(Paragraph("OBSERVACIONES", self.styles["SectionTitle"]))
            elements.append(Paragraph(observaciones, self.styles["InfoText"]))

        elements.append(Spacer(1, 8 * mm))
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=2 * mm))
        elements.append(Paragraph("Generado con <3 por chandelierp", self.styles["FooterText"]))

        return elements

    def generar_catalogo_pdf(self, productos: list) -> bytes:
        """Genera catálogo PDF con grid 2 columnas.

        Args:
            productos: list of dicts with keys:
                nombre (str), descripcion (Optional[str]),
                precio_venta (Decimal), imagen_s3_key (Optional[str])
        Returns:
            PDF bytes
        """
        from app.servicios.servicio_almacenamiento import ServicioAlmacenamiento

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            leftMargin=1.5 * cm,
            rightMargin=1.5 * cm,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
        )
        styles = self.styles
        primary = colors.HexColor(self.primary_color)
        storage = ServicioAlmacenamiento()
        story = []

        # ── Catalogue header: logo + company name + divider ──
        url_logo = self.tenant.get("url_logo")
        if url_logo:
            try:
                if url_logo.startswith("data:"):
                    _hdr, b64data = url_logo.split(",", 1)
                    img_bytes = base64.b64decode(b64data)
                    logo_img = RLImage(io.BytesIO(img_bytes), width=2 * cm, height=2 * cm)
                elif url_logo.startswith("/"):
                    static_base = os.path.join(os.path.dirname(__file__), "..", "..", "static")
                    logo_path = os.path.normpath(os.path.join(static_base, url_logo.replace("/static/", "", 1)))
                    logo_img = RLImage(logo_path, width=2 * cm, height=2 * cm)
                else:
                    img_bytes = storage.obtener_imagen_bytes(url_logo)
                    if img_bytes:
                        logo_img = RLImage(io.BytesIO(img_bytes), width=3 * cm, height=3 * cm)
                    else:
                        logo_img = None
                if logo_img:
                    logo_img.hAlign = "CENTER"
                    story.append(logo_img)
                    story.append(Spacer(1, 0.3 * cm))
            except Exception:
                pass

        story.append(Paragraph(self.tenant.get("nombre", "Catálogo de Productos"), styles["DocTitle"]))
        story.append(Paragraph("Catálogo de Productos", styles["DocSubtitle"]))
        from reportlab.platypus import HRFlowable

        story.append(HRFlowable(width="100%", thickness=1, color=primary, spaceAfter=4 * mm))
        story.append(Spacer(1, 0.3 * cm))

        # ── Product styles ──
        name_style = ParagraphStyle(
            "CatName",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            spaceAfter=2,
        )
        desc_style = ParagraphStyle(
            "CatDesc",
            parent=styles["Normal"],
            fontSize=7,
            fontName="Helvetica",
            spaceAfter=2,
            textColor=colors.HexColor("#555555"),
        )
        price_style = ParagraphStyle(
            "CatPrice",
            parent=styles["Normal"],
            fontSize=9,
            fontName="Helvetica-Bold",
            textColor=primary,
        )

        def build_product_cell(p: dict) -> list:
            cell: list = []
            # Try S3 image
            if p.get("imagen_s3_key") and storage.is_enabled:
                img_bytes = storage.obtener_imagen_bytes(p["imagen_s3_key"])
                if img_bytes:
                    try:
                        cell.append(RLImage(io.BytesIO(img_bytes), width=3.5 * cm, height=3.5 * cm))
                    except Exception:
                        pass
            cell.append(Paragraph(p.get("nombre", ""), name_style))
            if p.get("descripcion"):
                desc = (p["descripcion"] or "")[:80]
                cell.append(Paragraph(desc, desc_style))
            # precio_venta is Decimal — f-string handles it natively
            precio = p.get("precio_venta", 0)
            cell.append(Paragraph(f"${precio:,.0f}", price_style))
            return cell

        # ── 2-column grid ──
        rows = []
        for i in range(0, len(productos), 2):
            left = build_product_cell(productos[i])
            right = (
                build_product_cell(productos[i + 1]) if i + 1 < len(productos) else [Paragraph("", styles["Normal"])]
            )
            rows.append([left, right])

        if rows:
            table = Table(rows, colWidths=[9 * cm, 9 * cm])
            table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("PADDING", (0, 0), (-1, -1), 8),
                        ("LINEBELOW", (0, 0), (-1, -2), 0.5, colors.HexColor("#DDDDDD")),
                        ("LINEAFTER", (0, 0), (0, -1), 0.5, colors.HexColor("#DDDDDD")),
                    ]
                )
            )
            story.append(table)

        doc.build(story)
        return buffer.getvalue()

    def generar_factura_pdf(
        self,
        numero: str,
        fecha: str,
        cliente: dict,
        detalles: list,
        subtotal,
        descuento,
        base_gravable,
        total_iva,
        total,
        observaciones: Optional[str] = None,
        descuento_global_pct=None,
    ) -> bytes:
        """
        Genera un PDF de factura.

        Args:
            numero: Número de factura
            fecha: Fecha de emisión (string)
            cliente: Dict con info del cliente (nombre, numero_documento, etc.)
            detalles: Lista de dicts con info de cada línea
            subtotal, descuento, base_gravable, total_iva, total: Totales
            observaciones: Notas opcionales

        Returns:
            bytes del PDF generado
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

        elements = []
        elements.extend(self._build_header("FACTURA DE VENTA", numero, fecha))
        elements.extend(self._build_cliente_info(cliente))
        elements.extend(self._build_tabla_detalles(detalles))
        elements.extend(
            self._build_totales(
                subtotal, descuento, base_gravable, total_iva, total, descuento_global_pct=descuento_global_pct
            )
        )
        elements.extend(self._build_footer(observaciones))

        doc.build(elements)
        return buffer.getvalue()

    def generar_cotizacion_pdf(
        self,
        numero: str,
        fecha: str,
        fecha_vencimiento: str,
        cliente: dict,
        detalles: list,
        subtotal,
        descuento,
        base_gravable,
        total_iva,
        total,
        observaciones: Optional[str] = None,
        descuento_global_pct=None,
    ) -> bytes:
        """
        Genera un PDF de cotización.

        Returns:
            bytes del PDF generado
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            topMargin=1.5 * cm,
            bottomMargin=1.5 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

        elements = []
        elements.extend(self._build_header("COTIZACION", numero, fecha, fecha_vencimiento=fecha_vencimiento))
        elements.extend(self._build_cliente_info(cliente))
        elements.extend(self._build_tabla_detalles(detalles))
        elements.extend(
            self._build_totales(
                subtotal, descuento, base_gravable, total_iva, total, descuento_global_pct=descuento_global_pct
            )
        )
        elements.extend(self._build_footer(observaciones))

        doc.build(elements)
        return buffer.getvalue()
