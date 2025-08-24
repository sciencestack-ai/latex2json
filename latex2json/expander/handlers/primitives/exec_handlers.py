from latex2json.expander.expander_core import ExpanderCore

from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens import Token, TokenType
from latex2json.tokens.utils import is_whitespace_token, strip_whitespace_tokens


def newwrite_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok or not expander.is_control_sequence(tok):
        return None
    expander.consume()
    # ignore?
    return []


def write_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok:
        return None
    stream: str | int | None = None
    if expander.is_control_sequence(tok):
        # e.g. \write\@auxout
        stream = tok.value
        expander.consume()
    else:
        number = expander.parse_integer()
        if number is None:
            return None
        stream = number

    expander.skip_whitespace()
    # ignore?
    output = expander.parse_brace_as_tokens()
    return []


def openout_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    tok = expander.peek()
    if not tok or not expander.is_control_sequence(tok):
        return None
    expander.consume()
    expander.skip_whitespace()
    if not expander.parse_equals():
        return None
    expander.skip_whitespace()

    def stop_token_logic(tok: Token):
        if is_whitespace_token(tok):
            return True
        return False

    output = expander.process(stop_token_logic, consume_stop_token=False)
    return []


def register_exec_handlers(expander: ExpanderCore):
    expander.register_handler("\\write", write_handler, is_global=True)
    expander.register_handler("\\newwrite", newwrite_handler, is_global=True)
    expander.register_handler("\\openout", openout_handler, is_global=True)

    # ignore patterns
    ignore_patterns = {"immediate": 0, "closeout": "\\"}
    register_ignore_handlers_util(
        expander,
        ignore_patterns,
        expand=False,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_exec_handlers(expander)
    text = r"""
    \makeatletter
    \openout\@auxout = test.aux
    \immediate\write\@auxout{test}
    \closeout\@auxout
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    print(out)
