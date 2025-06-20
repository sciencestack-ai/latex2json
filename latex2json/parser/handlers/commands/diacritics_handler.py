import unicodedata
from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser_core import Handler, ParserCore
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, Token, TokenType


ACCENT_MAP = {
    # Basic accents
    "'": "\N{COMBINING ACUTE ACCENT}",
    "`": "\N{COMBINING GRAVE ACCENT}",
    '"': "\N{COMBINING DIAERESIS}",
    "^": "\N{COMBINING CIRCUMFLEX ACCENT}",
    "~": "\N{COMBINING TILDE}",
    "=": "\N{COMBINING MACRON}",
    # Special letters
    "c": "\N{COMBINING CEDILLA}",
    "H": "\N{COMBINING DOUBLE ACUTE ACCENT}",
    "k": "\N{COMBINING OGONEK}",
    "b": "\N{COMBINING MACRON BELOW}",
    ".": "\N{COMBINING DOT ABOVE}",
    "d": "\N{COMBINING DOT BELOW}",
    "r": "\N{COMBINING RING ABOVE}",
    "u": "\N{COMBINING BREVE}",
    "v": "\N{COMBINING CARON}",
    # Extended commands
    "vec": "\N{COMBINING RIGHT ARROW ABOVE}",
    "dot": "\N{COMBINING DOT ABOVE}",
    "hat": "\N{COMBINING CIRCUMFLEX ACCENT}",
    "check": "\N{COMBINING CARON}",
    "breve": "\N{COMBINING BREVE}",
    "acute": "\N{COMBINING ACUTE ACCENT}",
    "grave": "\N{COMBINING GRAVE ACCENT}",
    "tilde": "\N{COMBINING TILDE}",
    "bar": "\N{COMBINING OVERLINE}",
    "ddot": "\N{COMBINING DIAERESIS}",
    # Special
    "not": "\N{COMBINING LONG SOLIDUS OVERLAY}",
}


def apply_accent(base_char: str, accent: str) -> str:
    """
    Apply a LaTeX accent to a base character using Unicode combining characters.
    Only applies to the first character of the input string.

    Args:
        base_char (str): The character(s) to be accented (only first char gets accent)
        accent (str): The LaTeX accent command (without backslash)

    Returns:
        str: The string with first character accented in normalized form
    """
    if not base_char:
        return base_char

    if accent not in ACCENT_MAP:
        return base_char

    # Split into first char and rest
    first_char = base_char[0]
    rest = base_char[1:]

    # Combine only the first character with the accent and normalize
    combined = first_char + ACCENT_MAP[accent]
    return unicodedata.normalize("NFC", combined) + rest


def make_diacritics_handler(accent: str) -> Handler:
    def handler(parser: ParserCore, token: Token):
        if parser.is_math_mode:
            return [CommandNode(token.value)]
        char = ""
        parser.skip_whitespace()
        tok = parser.peek()
        if not tok:
            return []

        if tok == BEGIN_BRACE_TOKEN:
            nodes = parser.parse_brace_as_nodes()
            if nodes:
                nodes = strip_whitespace_nodes(nodes)
                if nodes and isinstance(nodes[0], TextNode):
                    text_str = nodes[0].text
                    nodes[0].text = apply_accent(text_str, accent)
                return nodes
        elif tok.type == TokenType.CHARACTER:
            char = tok.value
            parser.consume()
            return [TextNode(apply_accent(char, accent))]
        return []

    return handler


def register_diacritics_handler(parser: ParserCore):
    for accent in ACCENT_MAP:
        parser.register_handler(accent, make_diacritics_handler(accent))


if __name__ == "__main__":
    from latex2json.parser import Parser

    parser = Parser()

    # Test cases
    test_strings = [
        r"\'{e} \'{e}",  # with braces
        r"\'e",  # without braces
        r"\c{c}",  # cedilla with braces
        r"\c c",  # cedilla with space
        r"\vec{x}",  # vector with braces
        r"\vec x",  # vector with space
        r"\'{e}llo",  # in word
        r"\grave{a}",  # with braces
        r"\grave a",  # without braces
        r"\.DOT",
        r"\.  {sss}",
        r"\vec  a \vec333",
        r"\vec{x}",
        r"\vec x",
        r"\vec3",
        # Test multiple vector accents in one string
        r"\vec{x}\vec y\vec3",
        # Test with numbers and other characters
        r"\vec333",
        r"\vec{333}",
        # Test other diacritical marks
        r"\dot{x}",
        r"\ddot{x}",
        r"\hat{x}",
        r"\bar{x}",
        r"\not{=}",
        r"\H{x}",
    ]

    text = r"\vec{33}"

    out = parser.parse(text)
