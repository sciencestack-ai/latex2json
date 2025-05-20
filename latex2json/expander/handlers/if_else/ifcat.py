from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import process_if_else_block
from latex2json.tokens.types import Token, TokenType


def ifcat_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    a = expander.consume()
    if a is None:
        expander.logger.warning("Warning: \\ifcat expects a token")
        return None

    output = expander.expand_tokens([a])

    if len(output) < 2:
        # no skipwhitespace!
        b = expander.consume()
        if b is None:
            expander.logger.warning("Warning: \\ifcat expects a 2nd token")
            return None
        output.extend(expander.expand_tokens([b]))

    is_equal = False
    if len(output) >= 2:
        is_equal = output[0].catcode == output[1].catcode
        # push the remaining tokens into the stream
        expander.stream.push_tokens(output[2:])

    tok = expander.peek()
    if tok is None:
        expander.logger.warning("Warning: No more tokens after \\ifcat{a}{b}")
        return None

    return process_if_else_block(expander, is_equal)


def register_ifcat(expander: ExpanderCore):
    expander.register_handler("\\ifcat", ifcat_handler)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
