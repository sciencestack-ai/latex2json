from typing import List
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.expander.handlers.for_loops.for_each_handler import (
    is_comma_token,
    replace_for_each_item_body,
)
from latex2json.expander.handlers.if_else.ifnum import evaluate_ifnum
from latex2json.tokens import Token, TokenType
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN
from latex2json.tokens.utils import split_tokens_by_predicate, strip_whitespace_tokens


def for_loop_handler(expander: ExpanderCore, token: Token):
    blocks = expander.parse_braced_blocks(4)
    if len(blocks) != 4:
        expander.logger.warning("Warning: \\forloop expects 4 blocks")
        return None

    counter_name_toks = expander.expand_tokens(blocks[0])
    start_value_toks = expander.expand_tokens(blocks[1])
    condition = blocks[2]
    body = blocks[3]

    counter_name_str = expander.convert_tokens_to_str(counter_name_toks).strip()
    if not counter_name_str:
        expander.logger.warning("Warning: \\forloop expects a counter name")
        return None

    start_value_str = expander.convert_tokens_to_str(start_value_toks).strip()
    start_value = 0
    try:
        start_value = int(start_value_str)
    except ValueError:
        expander.logger.warning(
            f"Warning: \\forloop expects an integer start value, got {start_value_str}"
        )
        return None

    expander.state.set_counter(counter_name_str, start_value)

    # push the condition back to expander so evaluate_ifnum
    all_tokens: List[Token] = []
    while not expander.eof():
        expander.push_tokens(condition)
        is_true, _ = evaluate_ifnum(expander, None)
        if not is_true:
            break

        all_tokens.extend(expander.expand_tokens(body))
        expander.state.add_to_counter(counter_name_str, 1)

    expander.push_tokens(all_tokens)
    return []


def is_at_nil_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "@nil"  # \@nil


def at_for_loop_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    list_tokens: List[Token] = []
    while not expander.eof():
        tokens = expander.process(is_at_nil_token, consume_stop_token=True)
        if tokens is None:
            break
        list_tokens.extend(tokens)

        # \@nil,\@nil\@@ is the end of the list. First \@nil is already consumed by the process()
        is_end_sequence = expander.parse_keyword_sequence(
            [",", r"\@nil", r"\@@"], skip_whitespaces=True
        )
        if is_end_sequence:
            break

    expander.skip_whitespace()
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            r"Warning: \@forloop expected variable after \@nil,\@nil\@@"
        )
        return None
    expander.consume()

    variable_token = tok

    # convert to \@for \var := {...} \do
    out_tokens = [
        Token(TokenType.CONTROL_SEQUENCE, "@for"),
        variable_token,
        *expander.convert_str_to_tokens(":="),
        BEGIN_BRACE_TOKEN.copy(),  # {
        *list_tokens,
        END_BRACE_TOKEN.copy(),  # }
        Token(TokenType.CONTROL_SEQUENCE, "do"),
    ]
    expander.push_tokens(out_tokens)
    return []


def register_for_loop_handler(expander: ExpanderCore):
    expander.register_handler("forloop", for_loop_handler, is_global=True)
    expander.register_handler("@forloop", at_for_loop_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_for_loop_handler(expander)

    text = r"""
\newcounter{x}
\forloop{x}{1}{\value{x} < 10}{ % value of x is 1...9
    \arabic{x}                  % print x in arabic notation
}
"""

    text = r"""
    \makeatletter
    \@forloop a,b,c,\@nil, \@nil \@@\myvar{[\myvar] }
""".strip()
    out = expander.expand(text)
    print(out)
