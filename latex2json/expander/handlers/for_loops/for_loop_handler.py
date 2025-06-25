from typing import List
from latex2json.expander.expander_core import RELAX_TOKEN, ExpanderCore
from latex2json.expander.handlers.if_else.ifnum import evaluate_ifnum
from latex2json.tokens import Token, TokenType


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


def register_for_loop_handler(expander: ExpanderCore):
    expander.register_handler("forloop", for_loop_handler, is_global=True)


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
    out = expander.expand(text)
    print(out)
