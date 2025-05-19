from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import process_if_else_block
from latex2json.tokens.types import Token, TokenType


def check_ifx_equals(expander: ExpanderCore) -> bool | None:
    expander.skip_whitespace()
    a = expander.consume()
    if a is None:
        expander.logger.warning("Warning: \\ifx expects a token")
        return None

    expander.skip_whitespace()
    b = expander.consume()
    if b is None:
        expander.logger.warning("Warning: \\ifx expects a 2nd token")
        return None

    definition_of_a = expander.convert_to_macro_definitions([a])
    definition_of_b = expander.convert_to_macro_definitions([b])

    return ExpanderCore.check_tokens_equal(definition_of_a, definition_of_b)


def ifx_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    is_equal = check_ifx_equals(expander)
    if is_equal is None:
        return None

    tok = expander.peek()
    if tok is None:
        expander.logger.warning("Warning: No more tokens after \\ifx{a}{b}")
        return None

    return process_if_else_block(expander, is_equal)


def register_ifx(expander: ExpanderCore):
    expander.register_handler("\\ifx", ifx_handler)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
    text = r"""
    \def\foo{FOO}
    \def\a{\foo}
    \def\b{\foo}
    \def\c{BAR}
    \def\d{BAR}

    \ifx\a\c
        SAME AB
        \ifx\a\c
            SAME AC
        \else
            DIFFERENT AC
        \fi
    \else
        DIFFERENT AC
        \ifx\b\d
            SAME BD
        \else
            DIFFERENT BD
        \fi
    \fi
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    # print(out)
