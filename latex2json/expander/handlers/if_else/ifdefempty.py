from typing import List, Optional
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.tokens.types import Token, TokenType
from latex2json.expander.expander_core import ExpanderCore


def ifdefempty_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    \ifdefempty{<macro>}{<true>}{<false>}
    """
    blocks = expander.parse_braced_blocks(3)

    if len(blocks) != 3:
        expander.logger.warning("Warning: \\ifdefempty expects 3 blocks")
        return None

    macro_block = blocks[0]
    if not macro_block or macro_block[0].type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning("Warning: \\ifdefempty expects a macro")
        return None

    block = blocks[2]

    macro = expander.get_macro(macro_block[0].value)
    if not macro:
        block = blocks[1]
    elif macro.is_user_defined and not macro.definition:
        block = blocks[1]

    expander.push_tokens(block)
    return []


def register_ifdefempty(expander: ExpanderCore):
    r"""Registers the \ifdefempty macro with the expander."""
    ifdefempty_macro = Macro(
        "ifdefempty", handler=ifdefempty_handler, type=MacroType.IF
    )
    expander.register_macro("\\ifdefempty", ifdefempty_macro, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ifdefempty(expander)
    test_with_star = r"""
    \def\truecmd{TRUE}
    \def\falsecmd{FALSE}
    \ifthenelse{1}{\truecmd}{\falsecmd}
    """.strip()

    out = expander.expand(test_with_star)
    print(out)
