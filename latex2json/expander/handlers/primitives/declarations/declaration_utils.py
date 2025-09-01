from typing import List, Optional, Tuple
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from latex2json.tokens.utils import is_begin_bracket_token


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
