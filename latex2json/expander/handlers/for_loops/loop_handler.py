from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.tokens import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def is_repeat_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "repeat"


def loop_handler(expander: ExpanderCore, token: Token):

    # parse the tokens until \repeat for the loop syntax/body
    tokens = expander.parse_tokens_until(is_repeat_token, consume_predicate=True)
    if not tokens:
        return []

    N = len(tokens)

    if_macro = None
    if_tokens = []

    # check the final if condition right before \repeat (from reverse)
    for i in range(N - 1, -1, -1):
        tok = tokens[i]
        macro = expander.get_macro(tok)
        if isinstance(macro, IfMacro):
            if_macro = macro
            if_tokens = tokens[i:]
            tokens = tokens[:i]

            break

    all_tokens = strip_whitespace_tokens(expander.expand_tokens(tokens))

    # now check the if condition to see if repeats
    if if_tokens and if_macro:
        while not expander.eof():
            # check the if condition
            expander.push_tokens(if_tokens[1:])
            is_repeat, _ = if_macro.evaluate_condition(expander, if_tokens[0])

            if not is_repeat:
                break

            all_tokens.extend(strip_whitespace_tokens(expander.expand_tokens(tokens)))

    expander.push_tokens(all_tokens)
    return []


def register_loop_handlers(expander: ExpanderCore):
    expander.register_handler("loop", loop_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_loop_handlers(expander)

    text = r"""
\newcount\mycount
\mycount=1
\loop
  Item \the\mycount
  \advance\mycount by 1
\ifnum\mycount<3
\repeat
"""
    out = expander.expand(text)
    print(out)
