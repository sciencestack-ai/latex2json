from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import split_tokens_by_predicate, strip_whitespace_tokens
from latex2json.expander.handlers.for_loops.for_each_handler import (
    replace_for_each_item_body,
    is_comma_token,
)


def is_do_token(tok: Token) -> bool:
    return tok.type == TokenType.CONTROL_SEQUENCE and tok.value == "do"


def for_do_handler(expander: ExpanderCore, token: Token):
    r"""
    \@for\item:={apple,banana,cherry}\do{%
        \stepcounter{mycount}%
        \themycount. \item \\
    }

    Or 
    \@for\@tempa:=-1,0,1,2,3,4,5\do{ ... }
    """
    expander.skip_whitespace()

    tok = expander.peek()
    if not tok or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(r"\@for expected control sequence after @for")
        return None

    variables = [tok]
    expander.consume()

    expander.skip_whitespace()
    if not expander.parse_keyword(":="):
        expander.logger.warning(r"\@for expected := after control sequence")
        return None

    expander.skip_whitespace()
    list_tokens = expander.parse_brace_as_tokens()  # for {...} case
    if list_tokens is None:
        # parse tokens until \do
        list_tokens = expander.process(is_do_token, consume_stop_token=False)

    if list_tokens is None:
        expander.logger.warning(r"\@for expected variables after :=")
        return None

    expander.skip_whitespace()
    # parse out \do token
    tok = expander.peek()
    if not tok or not is_do_token(tok):
        expander.logger.warning(r"\@for expected \\do after variables")
        return None
    expander.consume()  # consume \do token itself

    expander.skip_whitespace()
    body_tokens = expander.parse_brace_as_tokens()
    if body_tokens is None:
        expander.logger.warning(r"\@for expected body after \\do")
        return None
    elif len(body_tokens) == 0:
        return []

    # split list tokens into groups by ','
    list_items = split_tokens_by_predicate(list_tokens, is_comma_token)

    result_tokens: List[Token] = []
    for item in list_items:
        out_tokens = replace_for_each_item_body(body_tokens, variables, [item])
        result_tokens.extend(out_tokens)

    expander.push_tokens(result_tokens)
    return []


def register_for_do_handler(expander: ExpanderCore):
    expander.register_handler("@for", for_do_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    text = r"""
    \makeatletter
    \@for\item:={apple,banana,cherry}\do{%
        \item \\
    }
    """

    expander = Expander()
    register_for_do_handler(expander)
    out = expander.expand(text)
