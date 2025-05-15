import enum
from typing import Dict


# https://en.wikibooks.org/wiki/TeX/catcode
class Catcode(enum.IntEnum):
    """LaTeX Category Codes."""

    ESCAPE = 0  # \
    BEGIN_GROUP = 1  # {
    END_GROUP = 2  # }
    MATH_SHIFT = 3  # $
    ALIGNMENT_TAB = 4  # &
    END_OF_LINE = 5  # Newline
    PARAMETER = 6  # #
    SUPERSCRIPT = 7  # ^
    SUBSCRIPT = 8  # _
    IGNORED = 9  # Null character
    SPACE = 10  # Space, Tab
    LETTER = 11  # a-z, A-Z
    OTHER = 12  # 0-9, [], punctuation etc.
    ACTIVE = 13  # ~
    COMMENT = 14  # %
    INVALID = 15  # Delete character


# Default catcode mapping (character code -> Catcode enum)
DEFAULT_CATCODES: Dict[int, Catcode] = {
    ord("\\"): Catcode.ESCAPE,
    ord("{"): Catcode.BEGIN_GROUP,
    ord("}"): Catcode.END_GROUP,
    ord("$"): Catcode.MATH_SHIFT,
    ord("&"): Catcode.ALIGNMENT_TAB,
    ord("#"): Catcode.PARAMETER,
    ord("^"): Catcode.SUPERSCRIPT,
    ord("_"): Catcode.SUBSCRIPT,
    ord(" "): Catcode.SPACE,
    ord("\t"): Catcode.SPACE,
    ord("\n"): Catcode.END_OF_LINE,
    ord("\r"): Catcode.END_OF_LINE,
    ord("%"): Catcode.COMMENT,
    ord("~"): Catcode.ACTIVE,
}

# Populate default catcodes for letters and digits
for i in range(ord("a"), ord("z") + 1):
    DEFAULT_CATCODES[i] = Catcode.LETTER
for i in range(ord("A"), ord("Z") + 1):
    DEFAULT_CATCODES[i] = Catcode.LETTER
for i in range(ord("0"), ord("9") + 1):
    DEFAULT_CATCODES[i] = Catcode.OTHER
# Add other common Catcode.OTHER characters (punctuation etc.)
for char in ".,:;!?-+/=()[]<>|`'*\"":
    if ord(char) not in DEFAULT_CATCODES:
        DEFAULT_CATCODES[ord(char)] = Catcode.OTHER

# Note: You would import DEFAULT_CATCODES in your tokenizer if you initialize with defaults


def get_default_catcodes() -> Dict[int, Catcode]:
    return DEFAULT_CATCODES.copy()
