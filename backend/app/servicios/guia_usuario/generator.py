"""
Main PDF generator for user guide.
Creates professional multi-page PDF documents with table of contents.
"""

import io
from datetime import date
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus.tableofcontents import TableOfContents


class GeneratorGuiaUsuario:
    """
    Main PDF generator for user guide documents.

    Usage:
        gen = GeneratorGuiaUsuario('guia_usuario.pdf')
        gen.add_title_page('Guía de Usuario chandelierp', 'Versión 1.0 - Febrero 2026')
        gen.add_toc()

        # Add chapters
        from chapter import ChapterBuilder
        chapter = ChapterBuilder('1. Inicio Rápido', styles)
        chapter.add_intro('Contenido...')
        gen.add_chapter(chapter)

        gen.build()

        # Or get as bytes
        pdf_bytes = gen.generate()
    """

    def __init__(self, output_path: str):
        """
        Initialize the PDF generator.

        Args:
            output_path: Path where the PDF will be saved
        """
        self.output_path = output_path
        self.elements = []
        self._styles = None
        self._chapters = []

        # Create the document with A4 and 2cm margins
        self.doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

    @property
    def styles(self):
        """Lazy-load styles."""
        if self._styles is None:
            from backend.app.servicios.guia_usuario.styles import get_styles

            self._styles = get_styles()
        return self._styles

    def add_title_page(
        self, title: str, subtitle: str, version: Optional[str] = None, tenant_name: str = "chandelierp"
    ) -> "GeneratorGuiaUsuario":
        """
        Add a cover/title page to the document.

        Args:
            title: Main title
            subtitle: Subtitle or description
            version: Version string
            tenant_name: Company/system name

        Returns:
            self for chaining
        """
        # Large title centered
        self.elements.append(Spacer(1, 4 * cm))
        self.elements.append(Paragraph(title, self.styles["CoverTitle"]))
        self.elements.append(Spacer(1, 0.5 * cm))

        # Subtitle
        self.elements.append(Paragraph(subtitle, self.styles["CoverSubtitle"]))

        # Version and date
        self.elements.append(Spacer(1, 2 * cm))

        version_text = version or f"Versión 1.0 - {date.today().strftime('%B %Y').title()}"
        self.elements.append(Paragraph(version_text, self.styles["CoverVersion"]))

        # System name
        self.elements.append(Spacer(1, 3 * cm))
        self.elements.append(Paragraph("Sistema ERP/POS multi-tenant para microempresas", self.styles["GuideSubtitle"]))

        # Footer
        self.elements.append(Spacer(1, 4 * cm))
        self.elements.append(Paragraph(f"© {date.today().year} {tenant_name}", self.styles["Note"]))

        # Page break after title page
        self.elements.append(PageBreak())

        return self

    def add_toc(self, title: str = "Tabla de Contenidos") -> "GeneratorGuiaUsuario":
        """
        Add a table of contents to the document.

        Args:
            title: Title for the TOC section

        Returns:
            self for chaining
        """
        # TOC title
        self.elements.append(Paragraph(title, self.styles["TOCTitle"]))
        self.elements.append(Spacer(1, 0.3 * cm))

        # Create TOC with level styles
        toc = TableOfContents()
        toc.tabLevel = 0

        # Level styles for TOC entries
        toc.levelStyles = [
            # Level 0 - Chapter titles (Heading1)
            self.styles["ChapterTitle"],
            # Level 1 - Section titles (Heading2)
            self.styles["SectionTitle"],
        ]

        self.elements.append(toc)

        # Page break after TOC
        self.elements.append(PageBreak())

        return self

    def add_chapter(self, chapter_builder) -> "GeneratorGuiaUsuario":
        """
        Add a pre-built chapter to the document.

        Args:
            chapter_builder: ChapterBuilder instance with content

        Returns:
            self for chaining
        """
        # Get elements from the chapter builder
        chapter_elements = chapter_builder.build()
        self.elements.extend(chapter_elements)

        # Add page break after chapter
        self.elements.append(PageBreak())

        return self

    def add_page_break(self) -> "GeneratorGuiaUsuario":
        """
        Add a manual page break.

        Returns:
            self for chaining
        """
        self.elements.append(PageBreak())
        return self

    def add_spacer(self, height: float = 0.5) -> "GeneratorGuiaUsuario":
        """
        Add vertical space.

        Args:
            height: Height in centimeters

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, height * cm))
        return self

    def build(self) -> None:
        """
        Build and save the PDF document.
        """
        # Enable bookmarks for PDF reader navigation
        self.doc.build(
            self.elements,
            onFirstPage=self._add_page_number,
            onLaterPages=self._add_page_number,
        )

    def generate(self) -> bytes:
        """
        Generate the PDF and return as bytes.

        Returns:
            PDF content as bytes
        """
        buffer = io.BytesIO()

        # Create a temporary doc to build to buffer
        temp_doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            topMargin=2 * cm,
            bottomMargin=2 * cm,
            leftMargin=2 * cm,
            rightMargin=2 * cm,
        )

        temp_doc.build(
            self.elements,
            onFirstPage=self._add_page_number,
            onLaterPages=self._add_page_number,
        )

        return buffer.getvalue()

    def _add_page_number(self, canvas, doc):
        """
        Add page numbers to the document.

        Args:
            canvas: ReportLab canvas
            doc: Document template
        """
        page_num = canvas.getPageNumber()
        text = f"Página {page_num}"

        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#6B7280"))

        # Center the page number
        canvas.drawCentredString(doc.pagesize[0] / 2, 1 * cm, text)


def create_sample_guide(output_path: str = "guia_ejemplo.pdf") -> None:
    """
    Create a sample user guide for testing.

    Args:
        output_path: Path where PDF will be saved
    """
    from backend.app.servicios.guia_usuario.styles import get_styles
    from backend.app.servicios.guia_usuario.templates.chapter import ChapterBuilder

    # Initialize generator
    gen = GeneratorGuiaUsuario(output_path)
    styles = get_styles()

    # Add title page
    gen.add_title_page(title="Guía de Usuario", subtitle="chandelierp", version="Versión 1.0")

    # Add TOC
    gen.add_toc()

    # Add sample chapter
    chapter = ChapterBuilder("1. Inicio Rápido", styles)
    chapter.add_intro(
        "En esta guía aprenderás a utilizar chandelierp para gestionar "
        "tu empresa de manera eficiente. El sistema está diseñado para microempresas "
        "colombianas del sector de candelería."
    )

    chapter.add_section(
        "1.1 Primer Inicio de Sesión",
        "Para comenzar a utilizar el sistema, ingresa tus credenciales de acceso. "
        "Si eres un nuevo usuario, el administrador de tu empresa te habrá proporcionado "
        "tu usuario y contraseña.",
    )

    chapter.add_step_list(
        [
            "Ingresa tu correo electrónico en el campo usuario",
            "Ingresa tu contraseña",
            "Haz clic en 'Iniciar Sesión'",
            "Selecciona el tenant (empresa) al que deseas acceder",
        ]
    )

    chapter.add_screenshot_placeholder("Pantalla de inicio de sesión")

    chapter.add_section(
        "1.2 Cambiar Contraseña",
        "Por seguridad, se recomienda cambiar la contraseña periódicamente. "
        "Para hacerlo, dirígete a Configuración > Mi Cuenta.",
    )

    # Add chapter to document
    gen.add_chapter(chapter)

    # Add another sample chapter
    chapter2 = ChapterBuilder("2. Productos e Inventario", styles)
    chapter2.add_intro("En este capítulo aprenderás a gestionar tus productos e inventarios de manera eficiente.")

    features = [
        {"name": "Crear productos", "description": "Agregar nuevos productos al catálogo", "available": True},
        {"name": "Editar productos", "description": "Modificar información de productos", "available": True},
        {"name": "Stock automático", "description": "Control automático de inventario", "available": True},
        {"name": "Alertas de stock", "description": "Notificaciones cuando el stock está bajo", "available": True},
    ]

    chapter2.add_feature_table(features)
    gen.add_chapter(chapter2)

    # Build PDF
    gen.build()
    print(f"PDF de ejemplo creado: {output_path}")


if __name__ == "__main__":
    create_sample_guide()
