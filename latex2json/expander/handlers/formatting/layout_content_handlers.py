from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens import Token
from latex2json.tokens.types import TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def two_column_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    out_tokens = expander.parse_bracket_as_tokens(expand=True)
    return out_tokens


def texorpdfstring_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2, expand=True)
    if len(blocks) != 2:
        expander.logger.warning("Expected 2 blocks for \\texorpdfstring")
        return []
    # choose the second block
    return blocks[1]


def intertext_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # intertext is somewhat the equivalent of \\ \text{...} \notag \\ ...
    block = expander.parse_immediate_token(expand=True, skip_whitespace=True) or []

    output_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, "\\"),
        Token(TokenType.CONTROL_SEQUENCE, "text"),
        *wrap_tokens_in_braces(block),
        Token(TokenType.CONTROL_SEQUENCE, "notag"),
        Token(TokenType.CONTROL_SEQUENCE, "\\"),
    ]
    expander.push_tokens(output_tokens)
    return []


def register_layout_content_handlers(expander: ExpanderCore):
    # columns
    expander.register_handler("onecolumn", lambda expander, token: [], is_global=True)
    expander.register_handler("twocolumn", two_column_handler, is_global=True)
    # texorpdfstring
    expander.register_handler("texorpdfstring", texorpdfstring_handler, is_global=True)
    # intertext
    expander.register_handler("intertext", intertext_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_layout_content_handlers(expander)
