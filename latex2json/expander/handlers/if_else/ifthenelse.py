from typing import List, Optional
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore


def if_then_else_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Evaluates \ifthenelse condition by checking if next token is an asterisk.
    Returns (True, None) if next token is *, (False, None) if not,
    or (None, error_msg) if there's an error.
    """
    blocks = expander.parse_braced_blocks(3, check_immediate_tokens=True)

    if len(blocks) != 3:
        expander.logger.warning("Warning: \\ifthenelse expects 3 blocks")
        return None

    eval_block = blocks[0]
    block = blocks[1]  # TODO:
    expander.push_tokens(block)
    return []


def register_ifthenelse(expander: ExpanderCore):
    r"""Registers the \ifthenelse macro with the expander."""
    if_then_macro = Macro("ifthenelse", handler=if_then_else_handler, type=MacroType.IF)
    expander.register_macro("\\ifthenelse", if_then_macro, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ifthenelse(expander)
    test_with_star = r"""
    \def\truecmd{TRUE}
    \def\falsecmd{FALSE}
    \ifthenelse{1}{\truecmd}{\falsecmd}
    """.strip()

    out = expander.expand(test_with_star)
    print(out)
