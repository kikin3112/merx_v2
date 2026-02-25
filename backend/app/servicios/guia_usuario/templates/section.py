"""
Section builder template for user guide.
Provides a reusable class for creating sub-sections within chapters.
"""

from typing import List

from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle


class SectionBuilder:
    """
    Builder for creating nested sections within chapters.

    Usage:
        section = SectionBuilder("1.1 Inicio de sesión", styles)
        section.add_content("Descripción del proceso...")
        section.add_step_list(["Paso 1", "Paso 2"])
        elements = section.build()
    """

    def __init__(self, title: str, style_dict: dict):
        """
        Initialize the section builder.

        Args:
            title: Section title (e.g., "1.1 Inicio de sesión")
            style_dict: Dictionary of styles from get_styles()
        """
        self.title = title
        self.style_dict = style_dict
        self.elements = []

    def add_content(self, text: str) -> "SectionBuilder":
        """
        Add content paragraph to the section.

        Args:
            text: Content text

        Returns:
            self for chaining
        """
        self.elements.append(Paragraph(text, self.style_dict["GuideBodyText"]))
        return self

    def add_step_list(self, steps: List[str]) -> "SectionBuilder":
        """
        Add numbered steps to the section.

        Args:
            steps: List of step descriptions

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.15 * cm))

        for i, step in enumerate(steps, 1):
            step_text = f"<b>Paso {i}:</b> {step}"
            self.elements.append(Paragraph(step_text, self.style_dict["GuideBodyText"]))
            self.elements.append(Spacer(1, 0.08 * cm))

        return self

    def add_subsection(self, subsection_title: str, content: str) -> "SectionBuilder":
        """
        Add a subsection with title and content.

        Args:
            subsection_title: Subsection heading
            content: Subsection content

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.15 * cm))

        # Use a smaller/bold style for subsections
        self.elements.append(Paragraph(f"<b>{subsection_title}</b>", self.style_dict["GuideBodyText"]))
        self.elements.append(Spacer(1, 0.1 * cm))
        self.elements.append(Paragraph(content, self.style_dict["GuideBodyText"]))

        return self

    def add_info_box(self, title: str, content: str, box_type: str = "info") -> "SectionBuilder":
        """
        Add an information box (info, warning, tip).

        Args:
            title: Box title
            content: Box content
            box_type: Type of box - "info", "warning", "tip"

        Returns:
            self for chaining
        """
        colors_map = {
            "info": colors.HexColor("#EBF5FF"),
            "warning": colors.HexColor("#FEF3C7"),
            "tip": colors.HexColor("#D1FAE5"),
        }

        border_colors_map = {
            "info": colors.HexColor("#3B82F6"),
            "warning": colors.HexColor("#F59E0B"),
            "tip": colors.HexColor("#10B981"),
        }

        bg_color = colors_map.get(box_type, colors_map["info"])
        border_color = border_colors_map.get(box_type, border_colors_map["info"])

        # Create a simple styled box using a table
        data = [[Paragraph(f"<b>{title}</b><br/>{content}", self.style_dict["GuideBodyText"])]]

        table = Table(data, colWidths=[14 * cm])
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), bg_color),
                    ("BOX", (0, 0), (-1, -1), 1, border_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 8),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ]
            )
        )

        self.elements.append(Spacer(1, 0.15 * cm))
        self.elements.append(table)

        return self

    def add_checklist(self, items: List[str]) -> "SectionBuilder":
        """
        Add a checklist with checkboxes.

        Args:
            items: List of checklist items

        Returns:
            self for chaining
        """
        self.elements.append(Spacer(1, 0.1 * cm))

        for item in items:
            # Using ☑ for checkbox representation
            self.elements.append(Paragraph(f"☐ {item}", self.style_dict["GuideBodyText"]))
            self.elements.append(Spacer(1, 0.05 * cm))

        return self

    def add_paragraph(self, text: str) -> "SectionBuilder":
        """
        Add a paragraph.

        Args:
            text: Paragraph text

        Returns:
            self for chaining
        """
        self.elements.append(Paragraph(text, self.style_dict["GuideBodyText"]))
        return self

    def add_spacer(self, height: float = 0.2) -> "SectionBuilder":
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
        Build the section elements.

        Returns:
            List of Platypus elements
        """
        result = []

        # Add section title
        result.append(Paragraph(self.title, self.style_dict["SectionTitle"]))

        # Add all content elements
        result.extend(self.elements)

        return result
