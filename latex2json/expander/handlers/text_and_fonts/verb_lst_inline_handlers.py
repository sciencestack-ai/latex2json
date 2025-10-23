from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens import Token, CommandWithArgsToken
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN


def verb_handler(expander: ExpanderCore, token: Token):
    expander.parse_asterisk()
    delim_token = expander.consume()
    if not delim_token:
        expander.logger.warning("\\verb expects a delimiter token")
        return None
    verb_tokens = expander.parse_tokens_until(
        lambda tok: tok == delim_token, consume_predicate=True, verbatim=True
    )
    return [CommandWithArgsToken("verb", [verb_tokens])]


def lst_inline_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    bracket_tokens = expander.parse_bracket_as_tokens(expand=False) or []

    expander.skip_whitespace()
    delim_token = expander.consume()
    if not delim_token:
        expander.logger.warning("\\lstinline expects a delimiter token")
        return None
    # note: lstinline also uses {...} as delimiter
    if delim_token == BEGIN_BRACE_TOKEN:
        delim_token = END_BRACE_TOKEN
    lst_inline_tokens = expander.parse_tokens_until(
        lambda tok: tok == delim_token, consume_predicate=True, verbatim=True
    )
    return [
        CommandWithArgsToken(
            "lstinline", [lst_inline_tokens], opt_args=[bracket_tokens]
        )
    ]


def register_verb_lst_inline_handlers(expander: ExpanderCore):
    expander.register_handler(r"\verb", verb_handler, is_global=True)
    expander.register_handler(r"\lstinline", lst_inline_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    out = expander.expand(r"\verb|Hello| POST")
    print(out)
