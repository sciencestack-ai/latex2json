from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType

from latex2json.expander.handlers.primitives.catcode import CatcodeHandler


def the_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    tok = expander.peek()
    if not tok:
        return None

    if tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\the expects a control sequence, but found {tok}"
        )
        return None

    name = tok.value

    if name == "catcode":
        expander.consume()
        return CatcodeHandler.getter(expander, token)
    else:
        # just expand the token
        parsed = expander.parse_register()
        if parsed:
            return expander.get_register_value_as_tokens(parsed[0], parsed[1])

    return []


def register_the(expander: ExpanderCore):
    expander.register_handler("\\the", the_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\the\catcode`\@")
