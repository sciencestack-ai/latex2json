from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, Token
from latex2json.tokens.utils import strip_whitespace_tokens


def noexpand_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handler for \noexpand primitive.

    \noexpand prevents the expansion of the next token in the input stream.
    Returns the next token unexpanded.
    """
    expander.skip_whitespace()
    return [expander.consume()]


def unexpanded_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handler for \unexpanded primitive.

    \unexpanded expands the next token in the input stream.
    Returns the next token unexpanded.
    """
    expander.skip_whitespace()
    brace = expander.parse_brace_as_tokens()
    if brace is None:
        expander.logger.warning("Warning: \\unexpanded expects a brace")
        return None
    return brace


def expandafter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handler for \expandafter primitive.

    \expandafter expands the token after the next token before the next token.
    The sequence \expandafter<token1><token2> will expand <token2> first,
    then process <token1>.
    """
    expander.skip_whitespace()
    tok1 = expander.consume()
    if tok1 is None:
        expander.logger.warning("Warning: \\expandafter expects 2 tokens")
        return None
    expander.skip_whitespace()
    tok2 = expander.peek()
    if tok2 is None:
        # \expandafter doesnt strictly need 2 tokens
        # put back tok1
        expander.push_tokens([tok1])
        return []

    # expand tok2
    expanded2 = expander.expand_next()
    # then put back tok1 and expanded2
    expander.push_tokens([tok1] + expanded2)
    return []


def register_expand_handlers(expander: ExpanderCore):
    """Register expansion-related primitive handlers."""
    expander.register_handler("\\noexpand", noexpand_handler, is_global=True)
    for expand_cmd in ["\\expandafter", "\\@xp"]:
        expander.register_handler(expand_cmd, expandafter_handler, is_global=True)
    expander.register_handler("\\unexpanded", unexpanded_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    out = expander.expand(r"\def\foo{FOO}\noexpand\foo")
    # print(out)

    text = r"""
    \def\ea{\expandafter}
    \ea\def\csname afoo\endcsname{AFOO}
    \afoo
""".strip()
    expander.expand(text)

    out = expander.expand(r"\afoo")
