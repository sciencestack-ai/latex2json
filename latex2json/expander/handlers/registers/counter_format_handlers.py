from typing import List, Optional, Callable
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.registers.counter_handlers import parse_counter_name
from latex2json.tokens import Token
from latex2json.expander.macro_registry import Macro


def _make_format_handler(
    format_name: str,
) -> Callable[[ExpanderCore, Token], Optional[List[Token]]]:
    """Factory function to create counter format handlers"""

    def handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        counter_name = parse_counter_name(expander)
        if not counter_name:
            expander.logger.warning(rf"\{format_name}: Missing counter name argument")
            return None

        value = expander.state.get_counter_as_format(counter_name, format_name)
        return expander.convert_str_to_tokens(value)

    return handler


def register_counter_format_handlers(expander: ExpanderCore):
    """Register all counter format handlers"""
    formats = ["roman", "Roman", "alph", "Alph", "arabic"]

    for format_name in formats:
        expander.register_macro(
            format_name,
            Macro(format_name, _make_format_handler(format_name), []),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_counter_format_handlers(expander)

    out = expander.expand(r"\setcounter{section}{4}\Alph{section}")
    print(out)
