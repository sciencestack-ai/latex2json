from typing import List, Optional, Protocol, Tuple
from latex2json.expander.macro_registry import Macro, MacroType
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


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
        super().__init__(name, type=MacroType.IF)
        self.evaluate_condition = evaluate_condition
        self.handler = lambda expander, token: self.expand(expander, token)

    def expand(self, expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        # Evaluate the condition
        is_true, error = self.evaluate_condition(expander, token)

        invalid = is_true is None
        if invalid:
            if error:
                expander.logger.warning(f"Warning: {error}")
            # don't return, continue to parse if-else blocks
            # return None

        blocks = parse_if_else_block_tokens(expander)
        if blocks is None or invalid:
            return []
        block = blocks[0] if is_true else blocks[1]

        # DONT expand immediately, since certain loops like \expandafter\xx\fi might expand prematurely
        # instead, push the block and let expander handle as continous sequence as usual
        expander.push_tokens(block)
        return []


def is_fi_command(token: Token) -> bool:
    if token.type == TokenType.CONTROL_SEQUENCE:
        return token.value == "fi"
    return False


def is_else_command(token: Token) -> bool:
    if token.type == TokenType.CONTROL_SEQUENCE:
        return token.value == "else"
    return False


# returns the block to execute if the condition is true/false
def parse_if_else_block_tokens(
    expander: ExpanderCore,
) -> Optional[Tuple[List[Token], List[Token]]]:
    tok = expander.peek()
    if tok is None:
        return None

    def is_if_command(token: Token) -> bool:
        if token.type == TokenType.CONTROL_SEQUENCE:
            macro = expander.get_macro(token.value)
            return isinstance(macro, IfMacro)
        return False

    # parse out the entire \if ... \fi block as RAW TOKENS (DONT PROCESS)
    block = expander.parse_begin_end_as_tokens(
        is_if_command, is_fi_command, check_first_token=False
    )
    if block is None:
        return None

    # add back the \fi since it is still a token and affects things like \expandafter e.g. \expandafter\somecmd\fi
    block += [Token(TokenType.CONTROL_SEQUENCE, "fi")]

    # Find the position of \else in the block
    else_pos = None
    nested_level = 0
    for i, token in enumerate(block):
        if token.type == TokenType.CONTROL_SEQUENCE:
            if is_if_command(token):
                nested_level += 1
            elif is_fi_command(token):
                nested_level -= 1
            elif is_else_command(token) and nested_level == 0:
                else_pos = i
                break

    true_block = block[:else_pos] if else_pos is not None else block
    false_block = block[else_pos + 1 :] if else_pos is not None else []

    return strip_whitespace_tokens(true_block), strip_whitespace_tokens(false_block)


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


def make_if_defined_eval(check_undefined=False) -> Macro:
    def evaluate_if_defined(
        expander: ExpanderCore, token: Token
    ) -> tuple[bool | None, str | None]:
        expander.skip_whitespace()
        tok = expander.consume()
        if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
            return None, "\\ifdefined expects a token"

        is_defined = expander.get_macro(tok.value) is not None
        if check_undefined:
            return not is_defined, None
        return is_defined, None

    return evaluate_if_defined


def evaluate_ifodd(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    expander.skip_whitespace()
    num = expander.parse_integer()
    if num is None:
        return None, "\\ifodd expects a number"

    return num % 2 == 1, None


def register_base_ifs(expander: ExpanderCore):
    expander.register_macro("\\if", IfMacro("if", evaluate_base_if), is_global=True)

    # else + fi (if we encounter these in the wild, it means our if handling went wrong)
    expander.register_handler("else", lambda expander, token: [], is_global=True)
    expander.register_handler("fi", lambda expander, token: [], is_global=True)

    # iftrue + iffalse
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

    # ifodd
    expander.register_macro(
        "\\ifodd",
        IfMacro("ifodd", evaluate_ifodd),
        is_global=True,
    )

    # ifdefined
    expander.register_macro(
        "\\ifdefined",
        IfMacro("ifdefined", make_if_defined_eval(check_undefined=False)),
        is_global=True,
    )
    expander.register_macro(
        "\\ifundefined",
        IfMacro("ifundefined", make_if_defined_eval(check_undefined=True)),
        is_global=True,
    )

    # eof
    expander.register_macro("\\ifeof", IfMacro("ifeof", evaluate_eof), is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

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
    POSTIF
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    print(out)
