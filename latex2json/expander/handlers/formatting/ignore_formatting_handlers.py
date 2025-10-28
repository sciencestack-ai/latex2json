from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.latex_maps.ignore_commands import IGNORE_PATTERNS
from latex2json.tokens.types import Token, TokenType


def vrule_hrule_handler(expander: ExpanderCore, token: Token):
    seen_keywords = set()
    dimensions = ["width", "height", "depth"]
    while True:
        expander.skip_whitespace()
        found_dimension = False
        for dim in dimensions:
            if dim not in seen_keywords and expander.parse_keyword(f"{dim} "):
                expander.parse_dimensions(parse_unknown=True)
                seen_keywords.add(dim)
                found_dimension = True
                break
        if not found_dimension:
            break
    return []


def newline_handler(expander: ExpanderCore, token: Token):
    # parse out any e.g. \\*[0.5em]
    expander.parse_keyword("*")
    space_cnt = expander.skip_whitespace_not_eol()
    if not expander.parse_bracket_as_tokens():
        # i.e. no \\ ... [0.5em]
        # push back the space tokens
        expander.push_text(" " * space_cnt)
    return [token]


def mathpalette_handler(expander: ExpanderCore, token: Token):
    toks1 = expander.parse_immediate_token(skip_whitespace=False, expand=False)
    if not toks1:
        expander.logger.warning(f"\\mathpalette expected argument but found nothing")
        return None

    # arbitrarily push a displaystyle token to stream
    style_token = Token(TokenType.CONTROL_SEQUENCE, value="displaystyle")
    expander.push_tokens(toks1 + [style_token])
    return []


def is_dollar_token(tok: Token) -> bool:
    return tok.type == TokenType.MATH_SHIFT_INLINE and tok.value == "$"


def rcsinfo_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok or not is_dollar_token(tok):
        expander.logger.info(f"\\rcsInfo expected math shift inline but found {tok}")
        return None
    expander.consume()
    tokens = expander.parse_tokens_until(is_dollar_token, consume_predicate=True)
    # ignore?
    return []


def big_handler(expander: ExpanderCore, token: Token):
    r"""
    It makes the following delimiter (like (, [, {, |, etc.) slightly larger than normal text size, but not as large as \Big, \bigg, or \Bigg

    We just ignore this command
    """
    # tokens = expander.parse_immediate_token(skip_whitespace=True, expand=True)
    return []


def register_ignore_format_handlers(expander: ExpanderCore):
    """Register all formatting-related command handlers"""
    register_ignore_handlers_util(expander, IGNORE_PATTERNS, expand=False)

    expander.register_handler(r"\vrule", vrule_hrule_handler, is_global=True)
    expander.register_handler(r"\hrule", vrule_hrule_handler, is_global=True)
    expander.register_handler(r"\mathpalette", mathpalette_handler, is_global=True)
    expander.register_handler(r"\rcsInfo", rcsinfo_handler, is_global=True)
    expander.register_handler(r"\\", newline_handler, is_global=True)

    for big in ["big", "Big", "bigg", "Bigg"]:
        expander.register_handler(big, big_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ignore_format_handlers(expander)

    # # Test some formatting commands
    # out1 = expander.expand(r"\floatname{figure}{Fig.}")
    # out2 = expander.expand(r"\pagestyle{fancy}")
    # out3 = expander.expand(
    #     r"\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}"
    # )
    # out4 = expander.expand(r"\vrule height 2pt depth -1.6pt width 23pt")

    out = expander.expand(r"\rcsInfo $Id: xxx$")
