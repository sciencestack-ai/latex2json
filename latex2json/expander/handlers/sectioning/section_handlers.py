from typing import List, Optional, Callable
from latex2json.expander.expander_core import ExpanderCore
from latex2json.latex_maps.sections import SECTIONS
from latex2json.tokens import (
    CommandWithArgsToken,
    Token,
)


def convert_numbering_to_upper_alphabet(numbering: str) -> str:
    # convert the first number to uppercase letter (1->A, 2->B, etc)
    number_split = numbering.split(".")
    first_num = int(number_split[0])
    # Convert to A, B, C etc (1->A, 2->B, etc)
    first_letter = chr(ord("A") + first_num - 1)
    number_split[0] = first_letter
    return ".".join(number_split)


def make_section_handler(
    cmd_name: str,
    counter_name: Optional[str] = None,
) -> Callable[[ExpanderCore, Token], Optional[List[CommandWithArgsToken]]]:
    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        has_asterisk = expander.parse_asterisk()
        expander.skip_whitespace()
        opt_arg = expander.parse_bracket_as_tokens()

        expander.skip_whitespace()
        content = expander.parse_brace_as_tokens(expand=True) or []

        numbering = None
        if (
            counter_name
            and not has_asterisk
            and expander.state.has_counter(counter_name)
        ):
            expander.state.step_counter(counter_name)  # e.g. section/subsection.. +1
            numbering = expander.state.get_counter_as_format(counter_name)

        # double check appendix
        if numbering and expander.state.in_appendix and cmd_name in SECTIONS:
            # convert the first number letter to upper alphabet
            numbering = convert_numbering_to_upper_alphabet(numbering)

        expanded_opt_args = []
        if opt_arg:
            exp_opt_arg = expander.expand_tokens(opt_arg)
            if exp_opt_arg:
                expanded_opt_args = [exp_opt_arg]

        out_token = CommandWithArgsToken(
            name=cmd_name,
            args=[content],
            opt_args=expanded_opt_args,
            numbering=numbering,
        )
        return [out_token]

    return handler


def appendix_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    # reset all section counters
    for cmd_name in SECTIONS:
        expander.state.set_counter(cmd_name, 0)

    expander.state.in_appendix = True
    return [token]  # return the raw token itself for parsing later


def register_section_handlers(expander: ExpanderCore):
    for cmd_name in SECTIONS:
        handler = make_section_handler(cmd_name, counter_name=cmd_name)
        expander.register_handler(
            cmd_name,
            handler,
            is_global=True,
        )

    for cmd_name in ["appendix", "appendices"]:
        expander.register_handler(
            cmd_name,
            appendix_handler,
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_section_handlers(expander)
    out = expander.expand(r"\def\xxx{XXX} \section*[BRO] {Hello \xxx \def\yyy{YYY}}")
