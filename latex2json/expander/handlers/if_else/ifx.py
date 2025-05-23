from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import Token, TokenType


def check_ifx_equals(a: Token, b: Token, expander: ExpanderCore) -> bool | None:
    a_macro: Macro | None = None
    b_macro: Macro | None = None

    if a.type == TokenType.CONTROL_SEQUENCE:
        a_macro = expander.get_macro(a.value)
        # if a is a \let, we need to get the first token in the definition
        if a_macro and a_macro.type == "let" and len(a_macro.definition) > 0:
            a = a_macro.definition[0]

    if b.type == TokenType.CONTROL_SEQUENCE:
        b_macro = expander.get_macro(b.value)
        if b_macro and b_macro.type == "let" and len(b_macro.definition) > 0:
            b = b_macro.definition[0]

    if a.type == TokenType.CONTROL_SEQUENCE and b.type == TokenType.CONTROL_SEQUENCE:
        # check if undefined
        undefined_a = a_macro is None
        undefined_b = b_macro is None
        if undefined_a and undefined_b:
            # both undefined, so they are equal in \ifx
            return True
        elif undefined_a or undefined_b:
            # one is undefined, so they are different in \ifx
            return False

        definition_of_a = expander.convert_to_macro_definitions([a])
        definition_of_b = expander.convert_to_macro_definitions([b])

        return ExpanderCore.check_tokens_equal(definition_of_a, definition_of_b)

    return ExpanderCore.check_tokens_equal([a], [b])


def evaluate_ifx(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    expander.skip_whitespace()
    a = expander.consume()
    if a is None:
        return None, "\\ifx expects a token"

    expander.skip_whitespace()
    b = expander.consume()
    if b is None:
        return None, "\\ifx expects a 2nd token"

    is_equal = check_ifx_equals(a, b, expander)
    if is_equal is None:
        return None, "Could not compare tokens"

    return is_equal, None


def register_ifx(expander: ExpanderCore):
    expander.register_macro("\\ifx", IfMacro("ifx", evaluate_ifx), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
    text = r"""
    \let\letcolon=:
    \def\defcolon{:}

    \ifx\letcolon: % true! 
        LET COLON
        \ifx\defcolon: % false! 
            DEF COLON
        \fi
    \fi

    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
