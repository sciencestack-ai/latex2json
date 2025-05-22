from typing import List, Optional, Protocol
from latex2json.expander.macro_registry import Macro
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType


class ConditionEvaluator(Protocol):
    """Protocol for condition evaluation functions"""

    def __call__(
        self, expander: ExpanderCore, token: Token
    ) -> tuple[bool | None, str | None]: ...


class IfMacro(Macro):
    """Base class for if-type macros that follow the pattern:
    1. Evaluate some condition
    2. Process if/else block based on condition
    """

    def __init__(self, name: str, evaluate_condition: ConditionEvaluator):
        super().__init__(name)
        self.evaluate_condition = evaluate_condition
        self.handler = lambda expander, token: self.expand(expander, token)

    def expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Evaluate the condition
        is_true, error = self.evaluate_condition(expander, token)

        if is_true is None:
            if error:
                expander.logger.warning(f"Warning: {error}")
            return None

        return process_if_else_block(expander, is_true)


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


def evaluate_base_if(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    expander.skip_whitespace()
    a = expander.consume()
    if a is None:
        return None, "\\if expects a token"

    expander.skip_whitespace()
    b = expander.consume()
    if b is None:
        return None, "\\if expects a 2nd token"

    return check_if_equals(a, b, expander), None


def evaluate_eof(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    return expander.eof(), None


def register_base_ifs(expander: ExpanderCore):
    expander.register_macro("\\if", IfMacro("if", evaluate_base_if), is_global=True)
    expander.register_macro(
        "\\iftrue",
        IfMacro("iftrue", lambda expander, token: (True, None)),
        is_global=True,
    )
    expander.register_macro(
        "\\iffalse",
        IfMacro("iffalse", lambda expander, token: (False, None)),
        is_global=True,
    )
    expander.register_macro("\\ifeof", IfMacro("ifeof", evaluate_eof), is_global=True)


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
