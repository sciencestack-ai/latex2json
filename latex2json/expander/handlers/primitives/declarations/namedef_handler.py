from typing import List, Optional

from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token, TokenType


def namedef_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    cmd_name = expander.parse_brace_name()
    if not cmd_name:
        expander.logger.warning("\\@namedef: Requires a name argument")
        return None

    # output \@namedef{cmd_name}... as \def\cmd_name...
    expander.push_tokens(
        [
            Token(TokenType.CONTROL_SEQUENCE, "def"),
            Token(TokenType.CONTROL_SEQUENCE, cmd_name),
        ]
    )

    return []


def register_namedef(expander: ExpanderCore):
    r"""Register the \@namedef command with the expander."""
    expander.register_macro(
        "\\@namedef",
        Macro("\\@namedef", namedef_handler),
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_namedef(expander)
    expander.expand(r"\makeatletter \@namedef{foo}{bar} \makeatother")
    out = expander.expand(r"\foo")
