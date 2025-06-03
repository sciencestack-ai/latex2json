from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token

import os


def input_handler(expander: ExpanderCore, token: Token):
    input_file = expander.parse_brace_name()
    if not input_file:
        expander.logger.warning("No input file provided")
        return None

    expander.push_file(input_file)
    return []


def register_file_input_handlers(expander: ExpanderCore):
    expander.register_handler(
        "input",
        input_handler,
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    out = expander.expand(
        r"\input{/Users/cj/Documents/python/latex2json/tests/test_data/sample.tex}"
    )
