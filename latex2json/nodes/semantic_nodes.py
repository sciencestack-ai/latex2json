from typing import List
from latex2json.nodes.base import ASTNode, check_children_equal


SECTION_LEVELS = {
    "part": 0,
    "chapter": 1,
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
}

PARAGRAPH_LEVELS = {
    "paragraph": 1,
    "subparagraph": 2,
}


def get_section_level(name: str) -> int:
    return SECTION_LEVELS.get(name.lstrip("\\"), 0)


def get_paragraph_level(name: str) -> int:
    return PARAGRAPH_LEVELS.get(name.lstrip("\\"), 0)


class SectionNode(ASTNode):
    def __init__(self, level: int, title: List[ASTNode], content: List[ASTNode] = []):
        self.level = level
        self.title = title
        self.content = content

    def __str__(self):
        out = f"Section({self.level}, {self.title})"
        if self.content:
            out += f" -> {self.content}"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, SectionNode):
            return False
        same = self.level == other.level and self.title == other.title
        if not same:
            return False
        return check_children_equal(self.content, other.content)


class ParagraphNode(ASTNode):
    def __init__(self, level: int, title: str, content: List[ASTNode] = []):
        self.level = level
        self.title = title
        self.content = content

    def __str__(self):
        out = f"Paragraph({self.level}, {self.title})"
        if self.content:
            out += f" -> {self.content}"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, ParagraphNode):
            return False
        same = self.level == other.level and self.title == other.title
        if not same:
            return False
        return check_children_equal(self.content, other.content)


LATEX_DIMENSION_UNITS = [
    "pt",  # Point (1/72.27 inch, exactly 1/864 of an American printer’s foot)
    "mm",  # Millimeter
    "cm",  # Centimeter
    "in",  # Inch
    "ex",  # Roughly the height of a lowercase 'x' in the current font
    "em",  # Roughly the width of an uppercase 'M' in the current font
    "mu",  # Math unit (1/18 em, where em is taken from the math symbols family)
    "sp",  # Scaled point (1/65536 pt, very precise, low-level unit)
    "bp",  # Big point (exactly 1/72 inch, used in PostScript)
    "pc",  # Pica (12 points, roughly 1/6 inch)
    "dd",  # Didot point (roughly 1.07 points, used in old European typography)
    "cc",  # Cicero (12 didot points)
    "nd",  # New Didot point (exactly 3/8 mm)
    "nc",  # New Cicero (12 new didot points)
    "px",  # Pixel (not standard in pure LaTeX, but supported in some modern packages)
    "zw",  # Ideographic character width (used in East Asian typesetting)
    "zh",  # Ideographic character height (also used in East Asian typesetting)
    "Q",  # Quarter millimeter (common in Japanese typography)
    "vw",  # Viewport width (from CSS, not standard in LaTeX)
    "vh",  # Viewport height (from CSS, not standard in LaTeX)
]


class DimensionNode(ASTNode):
    def __init__(self, value: float, unit: str):
        self.value = value
        self.unit = unit

    @staticmethod
    def is_valid_unit(unit: str) -> bool:
        return unit in LATEX_DIMENSION_UNITS

    def __str__(self):
        return f"Dimension({self.value} {self.unit})"
