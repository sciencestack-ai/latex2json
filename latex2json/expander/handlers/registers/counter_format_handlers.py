from typing import List, Optional, Callable
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.counter_handlers import parse_counter_name
from latex2json.registers.types import CounterFormat
from latex2json.tokens import Token
from latex2json.expander.macro_registry import Macro
from latex2json.tokens.types import TokenType


def _make_counter_format_handler(
    format_name: str,
) -> Callable[[ExpanderCore, Token], Optional[List[Token]]]:
    """Factory function to create counter format handlers"""

    counter_format = CounterFormat.from_str(format_name)

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        counter_name = parse_counter_name(expander)
        if not counter_name:
            expander.logger.warning(rf"\{format_name}: Missing counter name argument")
            return None

        value = expander.state.get_counter_value(counter_name)
        if value is None:
            return None
        value = counter_format.format_value(value)
        return expander.convert_str_to_tokens(value)

    return handler


def _make_at_counter_format_handler(
    format_name: str,
) -> Callable[[ExpanderCore, Token], Optional[List[Token]]]:
    r"""
    e.g. \@arabic\c@section
    \@arabic is the format, \c@section is the counter cmd
    """

    counter_format = CounterFormat.from_str(format_name)

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        expander.skip_whitespace()
        cmd = expander.parse_command_name_token()
        if not cmd:
            expander.logger.warning(rf"@{format_name}: Missing counter name argument")
            return None

        # strip out the c@ from the cmd.value
        cmd_name = cmd.value
        if cmd_name.startswith("c@"):
            cmd_name = cmd_name[2:]
        else:
            expander.logger.warning(
                rf"@{format_name}: Counter cmd must start with c@, got {cmd_name}"
            )
            return None

        value = expander.state.get_counter_value(cmd_name)
        if value is None:
            return None
        value = counter_format.format_value(value)
        return expander.convert_str_to_tokens(value)

    return handler


def register_counter_format_handlers(expander: ExpanderCore):
    """Register all counter format handlers"""
    formats = ["roman", "Roman", "alph", "Alph", "arabic"]

    for format_name in formats:
        expander.register_handler(
            format_name,
            _make_counter_format_handler(format_name),
            is_global=True,
        )
        expander.register_handler(
            "@" + format_name,
            _make_at_counter_format_handler(format_name),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_counter_format_handlers(expander)

    # out = expander.expand(r"\setcounter{section}{4}\Alph{section}")
    # print(out)

    text = r"""
    \makeatletter
    \section{s}
    \@arabic\c@section
"""
    out = expander.expand(text)
