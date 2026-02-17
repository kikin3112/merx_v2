"""
Definición de estilos de párrafo personalizados para la guía de usuario.
Usa los colores de marca de CLAUDE.md:
- Primary: #EC4899 (Rosa)
- Secondary: #8B5CF6 (Violeta)
- Success: #10B981, Warning: #F59E0B, Error: #EF4444
"""

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm


# Brand colors from CLAUDE.md
BRAND_PRIMARY = HexColor("#EC4899")  # Rosa
BRAND_SECONDARY = HexColor("#8B5CF6")  # Violeta
SUCCESS = HexColor("#10B981")
WARNING = HexColor("#F59E0B")
ERROR = HexColor("#EF4444")

# Neutral colors
GRAY_900 = HexColor("#111827")
GRAY_800 = HexColor("#1F2937")
GRAY_700 = HexColor("#374151")
GRAY_600 = HexColor("#4B5563")
GRAY_500 = HexColor("#6B7280")
GRAY_400 = HexColor("#9CA3AF")


def get_styles():
    """
    Returns a dictionary of custom paragraph styles for the user guide.

    Styles include:
    - Title: Main document title (24pt, brand primary, centered)
    - ChapterTitle: Chapter headings (18pt, gray-800, spaceBefore=30)
    - SectionTitle: Section headings (14pt, gray-700, spaceBefore=20)
    - BodyText: Main content (11pt, dark gray, justified, leading=16)
    - Note: Screenshot descriptions (10pt, gray-500, italic)
    - StepList: Numbered steps (11pt with bold "Paso N:" prefix)
    """
    styles = getSampleStyleSheet()

    # Title - Main document title
    styles.add(
        ParagraphStyle(
            name="GuideTitle",
            parent=styles["Title"],
            fontSize=24,
            textColor=BRAND_PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=30,
            spaceBefore=0,
        )
    )

    # Subtitle
    styles.add(
        ParagraphStyle(
            name="GuideSubtitle",
            parent=styles["Normal"],
            fontSize=14,
            textColor=GRAY_600,
            alignment=TA_CENTER,
            spaceAfter=40,
        )
    )

    # Chapter Title
    styles.add(
        ParagraphStyle(
            name="ChapterTitle",
            parent=styles["Heading1"],
            fontSize=18,
            textColor=GRAY_800,
            spaceBefore=30,
            spaceAfter=15,
            keepWithNext=True,
        )
    )

    # Section Title
    styles.add(
        ParagraphStyle(
            name="SectionTitle",
            parent=styles["Heading2"],
            fontSize=14,
            textColor=GRAY_700,
            spaceBefore=20,
            spaceAfter=10,
            keepWithNext=True,
        )
    )

    # Body Text - Main content (renamed to avoid conflict with sample stylesheet)
    styles.add(
        ParagraphStyle(
            name="GuideBodyText",
            parent=styles["Normal"],
            fontSize=11,
            textColor=HexColor("#333333"),
            leading=16,
            alignment=TA_JUSTIFY,
            spaceAfter=10,
        )
    )

    # Note - For screenshot descriptions
    styles.add(
        ParagraphStyle(
            name="Note",
            parent=styles["Normal"],
            fontSize=10,
            textColor=GRAY_500,
            fontName="Helvetica-Oblique",
            spaceBefore=5,
            spaceAfter=5,
        )
    )

    # Step List - Numbered steps
    styles.add(
        ParagraphStyle(
            name="StepList",
            parent=styles["Normal"],
            fontSize=11,
            textColor=HexColor("#333333"),
            leading=16,
            spaceAfter=8,
        )
    )

    # Feature Table Header
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["Normal"],
            fontSize=10,
            textColor=GRAY_900,
            fontName="Helvetica-Bold",
            alignment=TA_CENTER,
        )
    )

    # Feature Table Cell
    styles.add(
        ParagraphStyle(
            name="TableCell",
            parent=styles["Normal"],
            fontSize=10,
            textColor=HexColor("#333333"),
            alignment=TA_LEFT,
        )
    )

    # TOC Title
    styles.add(
        ParagraphStyle(
            name="TOCTitle",
            parent=styles["Heading1"],
            fontSize=16,
            textColor=GRAY_800,
            spaceBefore=20,
            spaceAfter=15,
        )
    )

    # Cover Page Title
    styles.add(
        ParagraphStyle(
            name="CoverTitle",
            parent=styles["Title"],
            fontSize=32,
            textColor=BRAND_PRIMARY,
            alignment=TA_CENTER,
            spaceAfter=10,
        )
    )

    # Cover Page Subtitle
    styles.add(
        ParagraphStyle(
            name="CoverSubtitle",
            parent=styles["Normal"],
            fontSize=18,
            textColor=GRAY_700,
            alignment=TA_CENTER,
            spaceAfter=30,
        )
    )

    # Cover Page Version
    styles.add(
        ParagraphStyle(
            name="CoverVersion",
            parent=styles["Normal"],
            fontSize=12,
            textColor=GRAY_500,
            alignment=TA_CENTER,
        )
    )

    return styles


# Export individual styles for convenience
def get_style_dict():
    """Returns styles as a dictionary for use with ChapterBuilder."""
    return get_styles()
