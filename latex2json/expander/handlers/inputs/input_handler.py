from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def input_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    input_file = expander.parse_brace_name()
    if not input_file:
        # try to parse until eol or relax
        input_file = expander.expand_until_eol_or_relax()
        if not input_file:
            expander.logger.warning("No input file provided")
            return None
        input_file = expander.convert_tokens_to_str(input_file)

    input_file = input_file.strip()
    expander.logger.info(f"Expanding input file: {input_file}")
    expander.push_file(input_file)
    return []


def endinput_handler(expander: ExpanderCore, token: Token):
    expander.stream.pop_source()
    return []


def register_file_input_handlers(expander: ExpanderCore):
    for command in ["input", "include"]:
        expander.register_handler(
            command,
            input_handler,
            is_global=True,
        )

    expander.register_handler("endinput", endinput_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    text = r"""
    
    \input ssss.sty
"""

    expander = Expander()
    out = expander.expand(text)
    # print(out)
