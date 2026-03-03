"""Factory for generating TF/T/F conditional handler variants.

expl3 conditionals follow a rigid pattern:
  - TF variant: evaluate, parse true branch, parse false branch, push winner
  - T variant:  evaluate, parse true branch, push if true
  - F variant:  evaluate, parse false branch, push if false

This factory eliminates the boilerplate. Supply an `evaluate` function that
parses the condition arguments and returns a bool, plus the number of extra
brace args to parse *before* the branches (e.g. str_if_eq has 2 comparison
args, tl_if_empty has 1 test arg), and the factory generates all three handlers.

Usage:
    def _eval_str_if_eq(expander, token):
        str1 = _parse_brace_str(expander)
        str2 = _parse_brace_str(expander)
        return str1 == str2

    str_if_eq_TF, str_if_eq_T, str_if_eq_F = make_conditional_handlers(_eval_str_if_eq)
"""

from typing import Callable, List, Optional, Tuple

from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


# evaluate(expander, token) -> bool
Evaluator = Callable[[ExpanderCore, Token], bool]


def make_conditional_handlers(
    evaluate: Evaluator,
) -> Tuple[
    Callable[[ExpanderCore, Token], Optional[List[Token]]],
    Callable[[ExpanderCore, Token], Optional[List[Token]]],
    Callable[[ExpanderCore, Token], Optional[List[Token]]],
]:
    """Return (TF_handler, T_handler, F_handler) for the given evaluator."""

    def tf_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        result = evaluate(expander, token)
        expander.skip_whitespace()
        true_branch = expander.parse_brace_as_tokens() or []
        expander.skip_whitespace()
        false_branch = expander.parse_brace_as_tokens() or []
        expander.push_tokens(true_branch if result else false_branch)
        return []

    def t_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        result = evaluate(expander, token)
        expander.skip_whitespace()
        true_branch = expander.parse_brace_as_tokens() or []
        if result:
            expander.push_tokens(true_branch)
        return []

    def f_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        result = evaluate(expander, token)
        expander.skip_whitespace()
        false_branch = expander.parse_brace_as_tokens() or []
        if not result:
            expander.push_tokens(false_branch)
        return []

    return tf_handler, t_handler, f_handler
