from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def input_handler(expander: ExpanderCore, token: Token):
    input_file = expander.parse_brace_name()
    if not input_file:
        expander.logger.warning("No input file provided")
        return None

    expander.logger.info(f"Expanding input file: {input_file}")
    expander.push_file(input_file)
    return []


def register_file_input_handlers(expander: ExpanderCore):
    for command in ["input", "include", "subfile", "subfileinclude"]:
        expander.register_handler(
            command,
            input_handler,
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    text = r"""
    
    \def\myinput{\input{/Users/cj/Documents/python/latex2json/tests/test_data/sample.tex}}
    
    For some \myinput

    POST 
"""

    expander = Expander()
    out = expander.expand(text)
    # print(out)
