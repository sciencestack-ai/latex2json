from typing import List, Optional, Tuple
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.expander.macro_registry import Macro
from latex2json.tokens import Token
from latex2json.expander.expander_core import ExpanderCore


def hvskip_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    """Handle and ignore skip commands."""
    expander.skip_whitespace()
    expander.parse_skip()

    return []


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
}


def register_skip_handlers(expander: ExpanderCore) -> None:
    """Register skip-related macros and handlers."""
    # Skip-related macros
    expander.register_handler(
        "hskip",
        hvskip_handler,
    )
    expander.register_handler(
        "vskip",
        hvskip_handler,
    )

    register_ignore_handlers_util(expander, ignored_skip_pattern_N_blocks)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_skip_handlers(expander)
    print(expander.expand(r"\hskip 10pt plus 10pt"))
    print(expander.expand(r"\smallskip 22"))
