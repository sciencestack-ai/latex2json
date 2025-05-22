from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.tokens.types import Token, TokenType


def evaluate_ifcat(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    expander.skip_whitespace()
    a = expander.consume()
    if a is None:
        return None, "\\ifcat expects a token"

    output = expander.expand_tokens([a])

    if len(output) < 2:
        # no skipwhitespace!
        b = expander.consume()
        if b is None:
            return None, "\\ifcat expects a 2nd token"
        output.extend(expander.expand_tokens([b]))

    if len(output) < 2:
        return None, "\\ifcat could not expand to two tokens"

    is_equal = output[0].catcode == output[1].catcode
    # push the remaining tokens into the stream
    expander.push_tokens(output[2:])

    return is_equal, None


def register_ifcat(expander: ExpanderCore):
    expander.register_macro("\\ifcat", IfMacro("ifcat", evaluate_ifcat), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
