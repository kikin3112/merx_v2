"""
CLI entry point for generating the complete user guide PDF.

Usage:
    python -m backend.app.servicios.guia_usuario
    python -m backend.app.servicios.guia_usuario -o my_guide.pdf
    python -m backend.app.servicios.guia_usuario --output my_guide.pdf

This module imports all chapter classes and generates a complete PDF user guide
with all 14 chapters, table of contents, and professional formatting.
"""

import argparse
import sys
from datetime import date

# Import all chapter classes
from backend.app.servicios.guia_usuario.chapters import (
    AccountingChapter,
    AuthChapter,
    BillingChapter,
    CRMChapter,
    DashboardChapter,
    MarginCalculatorChapter,
    PaymentsChapter,
    POSChapter,
    ProductsChapter,
    QuickStartChapter,
    QuotationsChapter,
    RecipesChapter,
    StorageChapter,
)
from backend.app.servicios.guia_usuario.generator import GeneratorGuiaUsuario
from backend.app.servicios.guia_usuario.styles import get_styles

VERSION = "1.0"
CHANDELIER_NAME = "ChandeliERP"


def generate_complete_guide(output_path: str = "guia_usuario.pdf") -> None:
    """
    Generate the complete user guide PDF with all chapters.

    Args:
        output_path: Path where the PDF will be saved
    """
    print(f"Generando guía de usuario: {output_path}")

    # Initialize generator
    gen = GeneratorGuiaUsuario(output_path)
    styles = get_styles()

    # Add title page
    print("  - Agregando página de título...")
    gen.add_title_page(
        title="Guía de Usuario ChandeliERP",
        subtitle="Sistema ERP/POS multi-tenant para microempresas",
        version=f"Versión {VERSION} - {date.today().strftime('%B %Y').title()}",
        tenant_name=CHANDELIER_NAME,
    )

    # Add table of contents
    print("  - Agregando tabla de contenidos...")
    gen.add_toc()

    # Initialize and add all chapters
    chapters = [
        ("Inicio Rápido", QuickStartChapter(styles)),
        ("Autenticación", AuthChapter(styles)),
        ("Productos e Inventario", ProductsChapter(styles)),
        ("Calculadora de Márgenes", MarginCalculatorChapter(styles)),
        ("CRM - Gestión de Clientes", CRMChapter(styles)),
        ("Cotizaciones", QuotationsChapter(styles)),
        ("Facturación", BillingChapter(styles)),
        ("Punto de Venta (POS)", POSChapter(styles)),
        ("Recetas (BOM)", RecipesChapter(styles)),
        ("Contabilidad", AccountingChapter(styles)),
        ("Dashboard y Reportes", DashboardChapter(styles)),
        ("Almacenamiento (Storage)", StorageChapter(styles)),
        ("Pagos Online (Wompi)", PaymentsChapter(styles)),
    ]

    print(f"  - Agregando {len(chapters)} capítulos...")

    for index, (title, chapter_instance) in enumerate(chapters, start=1):
        print(f"    {index}. {title}...")
        chapter_elements = chapter_instance.build()
        gen.elements.extend(chapter_elements)
        # Add page break after each chapter
        from reportlab.platypus import PageBreak

        gen.elements.append(PageBreak())

    # Build the PDF
    print("  - Generando PDF...")
    gen.build()

    print(f"\n✓ Guía de usuario creada exitosamente: {output_path}")

    # Print summary
    print("\nResumen:")
    print(f"  - Capítulos: {len(chapters)}")
    print(f"  - Versión: {VERSION}")
    print(f"  - Fecha: {date.today().strftime('%d/%m/%Y')}")


def main() -> None:
    """
    Main CLI entry point.
    """
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Genera la guía de usuario de ChandeliERP en formato PDF.",
        prog="python -m backend.app.servicios.guia_usuario",
    )

    parser.add_argument(
        "-o",
        "--output",
        default="guia_usuario.pdf",
        help="Ruta de salida para el PDF (default: guia_usuario.pdf)",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Muestra la versión del generador",
    )

    args = parser.parse_args()

    # Show version
    if args.version:
        print(f"Generador de Guía de Usuario - Versión {VERSION}")
        print(f"Sistema: {CHANDELIER_NAME}")
        sys.exit(0)

    # Generate the guide
    try:
        generate_complete_guide(args.output)
    except Exception as e:
        print(f"\n✗ Error al generar la guía: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
