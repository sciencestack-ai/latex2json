from typing import List, Optional, Tuple
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.macro_registry import Macro
from latex2json.tokens import Token
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import WHITESPACE_TOKEN, TokenType


def hskip_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    """Handle and ignore skip commands."""
    expander.skip_whitespace()
    expander.parse_skip()

    return [WHITESPACE_TOKEN.copy()]


def vskip_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"add \n just for this"
    expander.skip_whitespace()
    expander.parse_skip()

    return [Token(TokenType.END_OF_LINE, "\n")]


ignored_skip_pattern_N_blocks = {
    # Basic skips
    "smallskip": 0,
    "medskip": 0,
    "bigskip": 0,
    # Horizontal fills
    "hfil": 0,
    "hfill": 0,
    "hfilneg": 0,  # Negative hfil
    "hss": 0,  # Horizontal stretch/shrink
    # Vertical fills
    "vfil": 0,
    "vfill": 0,
    "vfilneg": 0,  # Negative vfil
    "vss": 0,  # Vertical stretch/shrink
    # MATH
    # Fixed math spaces (no arguments)
    "thinspace": 0,  # \, (3mu)
    "medspace": 0,  # \: (4mu)
    "thickspace": 0,  # \; (5mu)
    "negthinspace": 0,  # \! (-3mu)
    "negmedspace": 0,  # Negative medium space
    "negthickspace": 0,  # Negative thick space
}


def register_skip_handlers(expander: ExpanderCore) -> None:
    """Register skip-related macros and handlers."""
    # Skip-related macros
    for skips in ["hskip", "mskip"]:
        expander.register_handler(
            skips,
            hskip_handler,
        )
    expander.register_handler(
        "vskip",
        vskip_handler,
    )

    register_ignore_handlers_util(expander, ignored_skip_pattern_N_blocks)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_skip_handlers(expander)
    print(expander.expand(r"\hskip 10pt plus 10pt"))
    print(expander.expand(r"\smallskip 22"))
