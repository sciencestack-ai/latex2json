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


def check_if_equals(a: Token, b: Token, expander: ExpanderCore) -> bool:
    definition_of_a = expander.convert_to_macro_definitions([a])
    definition_of_b = expander.convert_to_macro_definitions([b])

    # if both are control sequences, only checks the first token of the output
    if a.type == TokenType.CONTROL_SEQUENCE and b.type == TokenType.CONTROL_SEQUENCE:
        return ExpanderCore.check_tokens_equal(definition_of_a[:1], definition_of_b[:1])

    return ExpanderCore.check_tokens_equal(definition_of_a, definition_of_b)


def base_if_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    a = expander.consume()
    if a is None:
        expander.logger.warning("Warning: \\if expects a token")
        return None

    expander.skip_whitespace()
    b = expander.consume()
    if b is None:
        expander.logger.warning("Warning: \\if expects a 2nd token")
        return None

    is_equal = check_if_equals(a, b, expander)
    return process_if_else_block(expander, is_equal)


def if_true_false_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    is_true = token.value == "iftrue"
    return process_if_else_block(expander, is_true)


def if_eof_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # TODO: can expander.eof() be used here?
    return process_if_else_block(expander, expander.eof())


def register_base_ifs(expander: ExpanderCore):
    expander.register_handler("\\if", base_if_handler, is_global=True)
    expander.register_handler("\\iftrue", if_true_false_handler, is_global=True)
    expander.register_handler("\\iffalse", if_true_false_handler, is_global=True)
    expander.register_handler("\\ifeof", if_eof_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
    text = r"""
    \iftrue
        TRUE
        \iffalse
            INNER TRUE
        \else
            INNER FALSE
        \fi
    \else
        FALSE
    \fi
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    print(out)
