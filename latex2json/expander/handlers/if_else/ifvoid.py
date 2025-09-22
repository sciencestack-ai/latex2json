from typing import List, Optional
from latex2json.registers.types import Box, RegisterType
from latex2json.tokens.types import Token, TokenType
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.tokens.utils import strip_whitespace_tokens


def evaluate_ifvoid(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    # Parse first number
    expander.skip_whitespace()
    tokens = expander.parse_immediate_token()
    if not tokens:
        return True, "\\ifvoid expects a box name"

    tok1 = tokens[0]
    box_id = int(tok1.value) if tok1.value.isdigit() else tok1.value.strip()
    box: Optional[Box] = expander.get_register_value(RegisterType.BOX, box_id)

    if box is None:
        return True, None

    box_is_void = not box.content
    return box_is_void, None


def register_ifvoid(expander: ExpanderCore):
    expander.register_macro(
        "\\ifvoid", IfMacro("ifvoid", evaluate_ifvoid), is_global=True
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()

    text = r"""
    \newbox\abstractbox
    \ifvoid\abstractbox
    TRUE
    \else
    FALSE
    \fi
"""
    out = expander.expand(text)

    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
