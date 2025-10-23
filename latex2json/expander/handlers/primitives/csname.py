from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_whitespace_token


def is_endcsname_command(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "endcsname"


def process_csname_block(
    expander: ExpanderCore,
) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None:
        return None

    block1 = expander.expand_until(is_endcsname_command, consume_stop_token=True)
    block1 = [b for b in block1 if not is_whitespace_token(b)]

    return block1


def csname_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handler for \csname primitive.

    \csname expands the next token in the input stream.
    """
    expander.skip_whitespace()

    block = process_csname_block(expander)
    if block is None:
        expander.logger.warning("\\csname expects a block ending with \\endcsname")
        return None

    str_name = expander.convert_tokens_to_str(block)
    control_sequence = Token(TokenType.CONTROL_SEQUENCE, str_name)
    expander.push_tokens([control_sequence])
    return []


def register_csname_handlers(expander: ExpanderCore):
    """Register expansion-related primitive handlers."""
    expander.register_handler("\\csname", csname_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_csname_handlers(expander)

    # print(expander.expand(r"\def\bar{bar}\csname foo\bar\endcsname"))

    text = r"""
\def\foo{foo}
\edef\foo{%
  \expandafter\noexpand\csname\foo\endcsname}
\foo
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
