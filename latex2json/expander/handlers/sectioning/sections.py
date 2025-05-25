from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import (
    Token,
    BEGIN_BRACKET_TOKEN,
    END_BRACKET_TOKEN,
    BEGIN_BRACE_TOKEN,
    END_BRACE_TOKEN,
)


def section_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    opt_arg = expander.parse_bracket_as_tokens()

    expander.skip_whitespace()
    content = expander.parse_brace_as_tokens()

    cmd_name = token.value
    expander.state.step_counter(cmd_name)  # e.g. section/subsection.. +1

    output_tokens: List[Token] = [token]  # e.g. \section
    if opt_arg is not None:
        expanded_opt_arg = expander.expand_tokens(opt_arg)
        output_tokens.extend(
            [BEGIN_BRACKET_TOKEN.copy(), *expanded_opt_arg, END_BRACKET_TOKEN.copy()]
        )

    if content is not None:
        expanded_content = expander.expand_tokens(content)
        output_tokens.extend(
            [
                BEGIN_BRACE_TOKEN.copy(),
                *expanded_content,
                END_BRACE_TOKEN.copy(),
            ]
        )

    return output_tokens


def register_section_handlers(expander: ExpanderCore):
    for cmd_name in [
        "part",
        "chapter",
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "subparagraph",
    ]:
        expander.register_macro(
            cmd_name,
            Macro(cmd_name, section_handler, []),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_section_handlers(expander)
    out = expander.expand(r"\def\xxx{XXX} \section [BRO] {Hello \xxx \def\yyy{YYY}}")
