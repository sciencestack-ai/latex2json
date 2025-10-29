# --- Define some basic attribute types (you'll expand these) ---
# Assuming these are enums or simple strings for now
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Dict


class FontStyleType(Enum):
    SERIES = auto()
    SHAPE = auto()
    SIZE = auto()
    FAMILY = auto()
    DECORATION = auto()
    TRANSFORM = auto()
    POSITION = auto()
    COLOR = auto()
    HIGHLIGHT = auto()


@dataclass
class FontStyle:
    type: FontStyleType
    value: str


class FontSeries:
    NORMAL = FontStyle(FontStyleType.SERIES, "normal")
    BOLD = FontStyle(FontStyleType.SERIES, "bold")


class FontShape:
    UPRIGHT = FontStyle(FontStyleType.SHAPE, "upright")
    ITALIC = FontStyle(FontStyleType.SHAPE, "italic")
    SLANTED = FontStyle(FontStyleType.SHAPE, "italic")  # slanted rendered as italic
    SMALL_CAPS = FontStyle(FontStyleType.SHAPE, "small-caps")


class FontSize:
    NORMAL = FontStyle(FontStyleType.SIZE, "normal")
    TINY = FontStyle(FontStyleType.SIZE, "xx-small")
    SCRIPTSIZE = FontStyle(FontStyleType.SIZE, "x-small")
    FOOTNOTESIZE = FontStyle(FontStyleType.SIZE, "small")
    SMALL = FontStyle(FontStyleType.SIZE, "small")
    NORMALSIZE = FontStyle(FontStyleType.SIZE, "medium")
    LARGE = FontStyle(FontStyleType.SIZE, "large")
    HUGE = FontStyle(FontStyleType.SIZE, "xx-large")


class FontFamily:
    ROMAN = FontStyle(FontStyleType.FAMILY, "normal")
    SANS = FontStyle(FontStyleType.FAMILY, "sans-serif")
    TYPEWRITER = FontStyle(FontStyleType.FAMILY, "monospace")


class FontDecoration:
    NONE = FontStyle(FontStyleType.DECORATION, "none")
    UNDERLINE = FontStyle(FontStyleType.DECORATION, "underline")
    OVERLINE = FontStyle(FontStyleType.DECORATION, "overline")
    LINE_THROUGH = FontStyle(FontStyleType.DECORATION, "line-through")


class FontTransform:
    NONE = FontStyle(FontStyleType.TRANSFORM, "none")
    UPPERCASE = FontStyle(FontStyleType.TRANSFORM, "uppercase")
    LOWERCASE = FontStyle(FontStyleType.TRANSFORM, "lowercase")


class FontPosition:
    NORMAL = FontStyle(FontStyleType.POSITION, "normal")
    SUPERSCRIPT = FontStyle(FontStyleType.POSITION, "superscript")
    SUBSCRIPT = FontStyle(FontStyleType.POSITION, "subscript")


# Mapping LaTeX commands to FontStyle objects
LATEX_TO_FONT_STYLE: Dict[str, FontStyle] = {
    # Series
    "textbf": FontSeries.BOLD,
    # Shape
    "textit": FontShape.ITALIC,
    "textsl": FontShape.SLANTED,
    "textsc": FontShape.SMALL_CAPS,
    "textup": FontShape.UPRIGHT,
    "emph": FontShape.ITALIC,
    # Family
    "textsf": FontFamily.SANS,
    "texttt": FontFamily.TYPEWRITER,
    "textrm": FontFamily.ROMAN,
    # Size
    "texttiny": FontSize.TINY,
    "textscriptsize": FontSize.SCRIPTSIZE,
    "textfootnotesize": FontSize.FOOTNOTESIZE,
    "textsmall": FontSize.SMALL,
    "textnormal": FontSize.NORMALSIZE,
    "textlarge": FontSize.LARGE,
    "texthuge": FontSize.HUGE,
    # Decoration
    "underbar": FontDecoration.UNDERLINE,
    "underline": FontDecoration.UNDERLINE,
    "overline": FontDecoration.OVERLINE,
    "textoverline": FontDecoration.OVERLINE,
    "textstrikeout": FontDecoration.LINE_THROUGH,
    "sout": FontDecoration.LINE_THROUGH,
    # Position
    "textsuperscript": FontPosition.SUPERSCRIPT,
    "textsubscript": FontPosition.SUBSCRIPT,
}

TEXT_MODE_COMMANDS = ["emph", "textcolor"]
for cmd in LATEX_TO_FONT_STYLE.keys():
    if cmd.startswith("text"):
        TEXT_MODE_COMMANDS.append(cmd)

# Direct mapping of legacy commands to FontStyle objects
LEGACY_TO_FONT_STYLE: Dict[str, FontStyle] = {
    # Basic text style commands
    "tt": FontFamily.TYPEWRITER,
    "bf": FontSeries.BOLD,
    "it": FontShape.ITALIC,
    "sl": FontShape.SLANTED,
    "sc": FontShape.SMALL_CAPS,
    "sf": FontFamily.SANS,
    "rm": FontFamily.ROMAN,
    "em": FontShape.ITALIC,
    "bold": FontSeries.BOLD,
    # Font family declarations
    "rmfamily": FontFamily.ROMAN,
    "sffamily": FontFamily.SANS,
    "ttfamily": FontFamily.TYPEWRITER,
    "opensans": FontFamily.SANS,
    # Font shape declarations
    "itshape": FontShape.ITALIC,
    "scshape": FontShape.SMALL_CAPS,
    "upshape": FontShape.UPRIGHT,
    "slshape": FontShape.SLANTED,
    # Font series declarations
    "bfseries": FontSeries.BOLD,
    "mdseries": FontSeries.NORMAL,
    # Font combinations and resets
    "normalfont": FontFamily.ROMAN,
    # Additional text mode variants
    "textup": FontShape.UPRIGHT,
    "textnormal": FontSize.NORMALSIZE,
    "textmd": FontSeries.NORMAL,
    # math stuff (often used directly before math mode)
    "unboldmath": FontSeries.NORMAL,
    "boldmath": FontSeries.BOLD,
    "bm": FontSeries.BOLD,
    # Size mappings
    "tiny": FontSize.TINY,
    "scriptsize": FontSize.SCRIPTSIZE,
    "footnotesize": FontSize.FOOTNOTESIZE,
    "small": FontSize.SMALL,
    "normalsize": FontSize.NORMALSIZE,
    "large": FontSize.LARGE,
    "Large": FontSize.LARGE,
    "LARGE": FontSize.LARGE,
    "huge": FontSize.HUGE,
    "Huge": FontSize.HUGE,
    "smaller": FontSize.SMALL,
    "larger": FontSize.LARGE,
}


@dataclass
class FontAttributes:
    """Represents the current font settings."""

    series: FontStyle = field(default_factory=lambda: FontSeries.NORMAL)
    shape: FontStyle = field(default_factory=lambda: FontShape.UPRIGHT)
    size: FontStyle = field(default_factory=lambda: FontSize.NORMAL)
    family: FontStyle = field(default_factory=lambda: FontFamily.ROMAN)
    decoration: FontStyle = field(default_factory=lambda: FontDecoration.NONE)
    transform: FontStyle = field(default_factory=lambda: FontTransform.NONE)
    position: FontStyle = field(default_factory=lambda: FontPosition.NORMAL)
    color: Optional[str] = None  # This one is fine as it's immutable
    highlight_color: Optional[str] = None

    def copy(self):
        return FontAttributes(
            series=self.series,
            shape=self.shape,
            size=self.size,
            family=self.family,
            decoration=self.decoration,
            transform=self.transform,
            position=self.position,
            color=self.color,
            highlight_color=self.highlight_color,
        )
