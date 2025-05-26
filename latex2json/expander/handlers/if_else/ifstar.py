from typing import List, Optional
from latex2json.tokens.types import Token
from latex2json.expander.expander_core import ExpanderCore


def if_star_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""
    Evaluates \ifstar condition by checking if next token is an asterisk.
    Returns (True, None) if next token is *, (False, None) if not,
    or (None, error_msg) if there's an error.
    """
    blocks = expander.parse_braced_blocks(2)

    if len(blocks) != 2:
        expander.logger.warning("Warning: \\@ifstar expects 2 blocks")
        return None

    has_star = expander.parse_asterisk()
    block = blocks[0] if has_star else blocks[1]
    expander.push_tokens(block)
    return []


def register_ifstar(expander: ExpanderCore):
    r"""Registers the \ifstar macro with the expander."""
    expander.register_handler("\\@ifstar", if_star_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ifstar(expander)
    test_with_star = r"""
    \makeatletter
    \def\cmd{\iftrue\@ifstar{star}{nostar}\fi} 
    \makeatother
    """.strip()

    expander.expand(test_with_star)
    out = expander.expand(r"\cmd*")  # star
