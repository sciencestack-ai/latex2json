from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


def is_else_command(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "else"


def is_fi_command(token: Token) -> bool:
    return token.type == TokenType.CONTROL_SEQUENCE and token.value == "fi"


def is_else_or_fi_command(token: Token) -> bool:
    return is_else_command(token) or is_fi_command(token)


# returns the block to execute if the condition is true/false
def process_if_else_block(
    expander: ExpanderCore, is_equal: bool
) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None:
        return None

    block1 = expander.process(is_else_or_fi_command)
    tok = expander.peek()
    if tok is None:
        if is_equal:
            return block1
        return []

    block2 = []
    if is_else_command(tok):
        expander.consume()  # consume the \else
        block2 = expander.process(is_fi_command)

    tok = expander.peek()
    if is_fi_command(tok):
        expander.consume()  # consume the \fi

    if is_equal:
        return block1

    return block2
