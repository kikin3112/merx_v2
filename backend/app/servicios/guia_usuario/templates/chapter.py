"""
Chapter builder template for user guide.
Provides a reusable class for creating chapters with sections, steps, and content.
"""

from typing import Any, Dict, List, Optional

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


class ChapterBuilder:
    """
    Builder for creating chapter content in the user guide.

    Usage:
        chapter = ChapterBuilder("1. Autenticación", styles)
        chapter.add_intro("En este capítulo aprenderás...")
        chapter.add_section("1.1 Inicio de sesión", "Contenido de la sección...")
        chapter.add_step_list(["Paso 1", "Paso 2", "Paso 3"])
        chapter.add_feature_table([...])
        elements = chapter.build()
    """

    def __init__(self, title: str, style_dict: dict):
        """
        Initialize the chapter builder.

        Args:
            title: Chapter title (e.g., "1. Autenticación")
            style_dict: Dictionary of styles from get_styles()
        """
        self.title = title
        self.style_dict = style_dict
        self.elements = []
        self._has_intro = False

    def add_intro(self, text: str) -> "ChapterBuilder":
        """
        Add chapter introduction text.

        Args:
            text: Introduction paragraph text

        Returns:
            self for chaining
        """
        if self._has_intro:
            self.elements.append(Spacer(1, 0.2 * cm))

        self.elements.append(Paragraph(text, self.style_dict["GuideBodyText"]))
        self._has_intro = True
        return self

    def add_section(self, section_title: str, content: str) -> "ChapterBuilder":
        """
        Add a titled section with content.

        Args:
            section_title: Section heading
            content: Section content text

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.2 * cm))
        self.elements.append(Paragraph(section_title, self.style_dict["SectionTitle"]))
        self.elements.append(Paragraph(content, self.style_dict["GuideBodyText"]))
        return self

    def add_screenshot_placeholder(self, description: str) -> "ChapterBuilder":
        """
        Add a styled box indicating where a screenshot should go.

        Args:
            description: Description of what the screenshot should show

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.1 * cm))
        self.elements.append(Paragraph(f"[IMAGEN: {description}]", self.style_dict["Note"]))
        return self

    def add_step_list(self, steps: List[str], title: Optional[str] = None) -> "ChapterBuilder":
        """
        Add numbered steps (Paso 1:, Paso 2:, etc.).

        Args:
            steps: List of step descriptions
            title: Optional title for the step list

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.2 * cm))

        if title:
            self.elements.append(Paragraph(title, self.style_dict["SectionTitle"]))

        for i, step in enumerate(steps, 1):
            step_text = f"<b>Paso {i}:</b> {step}"
            self.elements.append(Paragraph(step_text, self.style_dict["GuideBodyText"]))
            self.elements.append(Spacer(1, 0.1 * cm))

        return self

    def add_feature_table(
        self, features: List[Dict[str, Any]], columns: Optional[List[str]] = None
    ) -> "ChapterBuilder":
        """
        Add a table showing features and their availability.

        Args:
            features: List of dicts with keys: name, description, available
            columns: Column headers (default: ["Funcionalidad", "Descripción", "Disponible"])

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.3 * cm))

        if columns is None:
            columns = ["Funcionalidad", "Descripción", "Disponible"]

        # Build table data
        data = [columns]
        for feature in features:
            row = [
                feature.get("name", ""),
                feature.get("description", ""),
                "Sí" if feature.get("available", False) else "No",
            ]
            data.append(row)

        # Column widths
        col_widths = [4 * cm, 10 * cm, 3 * cm]

        table = Table(data, colWidths=col_widths)

        # Table styling
        style = TableStyle(
            [
                # Header row
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EC4899")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                # Body rows
                ("FONTSIZE", (0, 1), (-1, -1), 9),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("ALIGN", (0, 1), (0, -1), "LEFT"),
                ("ALIGN", (1, 1), (1, -1), "LEFT"),
                ("ALIGN", (2, 1), (2, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                # Grid
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E5E7EB")),
                # Row backgrounds
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ]
        )

        table.setStyle(style)
        self.elements.append(table)

        return self

    def add_paragraph(self, text: str, style: str = "GuideBodyText") -> "ChapterBuilder":
        """
        Add a paragraph with a specific style.

        Args:
            text: Paragraph text
            style: Style name from style_dict

        Returns:
            self for chaining
        """
        if style in self.style_dict:
            self.elements.append(Paragraph(text, self.style_dict[style]))
        else:
            self.elements.append(Paragraph(text, self.style_dict["GuideBodyText"]))
        return self

    def add_spacer(self, height: float = 0.3) -> "ChapterBuilder":
        """
        Add vertical space.

        Args:
            height: Height in centimeters

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, height * cm))
        return self

    def build(self) -> List:
        """
        Build the chapter elements.

        Returns:
            List of Platypus elements (Paragraph, Spacer, Table)
        """
        result = []

        # Add chapter title at the beginning
        result.append(Paragraph(self.title, self.style_dict["ChapterTitle"]))
        result.append(Spacer(1, 0.3 * cm))

        # Add all content elements
        result.extend(self.elements)

        return result
