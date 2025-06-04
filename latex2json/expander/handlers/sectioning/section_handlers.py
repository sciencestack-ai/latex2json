from typing import List, Optional, Callable
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.macro_registry import Macro
from latex2json.latex_maps.sections import SECTIONS
from latex2json.tokens import (
    CommandWithArgsToken,
    Token,
)


def make_section_handler(
    cmd_name: str,
    counter_name: Optional[str] = None,
) -> Callable[[ExpanderCore, Token], Optional[List[Token]]]:
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


def register_section_handlers(expander: ExpanderCore):
    for cmd_name in SECTIONS:
        handler = make_section_handler(cmd_name, counter_name=cmd_name)
        expander.register_macro(
            cmd_name,
            Macro(cmd_name, handler, []),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_section_handlers(expander)
    out = expander.expand(r"\def\xxx{XXX} \section*[BRO] {Hello \xxx \def\yyy{YYY}}")
