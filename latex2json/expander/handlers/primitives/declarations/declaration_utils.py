from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_begin_bracket_token, strip_whitespace_tokens


def is_self_referential_definition(
    cmd: Token, usage_pattern: List[Token], definition: List[Token]
) -> bool:
    r"""Detect \def\X{\X} (a no-op in our model, infinite loop otherwise).

    Shows up in older papers via guards like ``\def\mathbb{\Bbb}`` once ``\Bbb``
    has been rewritten to ``\mathbb`` by the AMSTeX preprocessor (see arXiv
    1012.3760).
    """
    if usage_pattern:
        return False
    body = strip_whitespace_tokens(list(definition))
    if len(body) != 1:
        return False
    tok = body[0]
    return (
        tok.type == TokenType.CONTROL_SEQUENCE
        and cmd.type == TokenType.CONTROL_SEQUENCE
        and tok.value == cmd.value
    )


def get_newcommand_args_and_definition(
    expander: ExpanderCore,
) -> Tuple[int, Optional[List[Token]], List[Token]]:
    # Parse optional number of arguments [n]
    num_args = 0
    default_arg = None

    expander.skip_whitespace()
    tok = expander.peek()
    if tok and is_begin_bracket_token(tok):
        arg_tokens = expander.parse_bracket_as_tokens()
        try:
            num_args = int("".join(t.value for t in arg_tokens))
        except ValueError:
            expander.logger.warning(
                f"invalid number of arguments: {''.join(t.value for t in arg_tokens)}"
            )
            return None

        # Parse optional default value for first argument
        expander.skip_whitespace()
        tok = expander.peek()
        if tok and is_begin_bracket_token(tok):
            default_arg = expander.parse_bracket_as_tokens()

    # Parse command definition
    expander.skip_whitespace()
    definition = expander.parse_immediate_token()

    if definition is None:
        return None

    return (num_args, default_arg, definition)
