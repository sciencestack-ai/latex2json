from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.count_handlers import CountHandler
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

    expander.consume()
    name = tok.value

    if name == "catcode":
        return CatcodeHandler.getter(expander, token)
    elif name == "count":
        return CountHandler.getter(expander, token)
    else:
        # just expand the token
        exp = expander.expand_tokens([tok])
        return exp

    return []


def register_the(expander: ExpanderCore):
    expander.register_handler("\\the", the_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    expander.expand(r"\the\catcode`\@")
