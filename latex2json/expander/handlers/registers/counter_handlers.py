from typing import List, Optional, Tuple
from latex2json.expander.macro_registry import Macro
from latex2json.expander.registers import RegisterType
from latex2json.tokens import Token
from latex2json.expander.expander_core import ExpanderCore


def _parse_counter_name(expander: ExpanderCore, brackets=False) -> Optional[str]:
    """Parse a counter name from braces and return its register name.
    Returns None if parsing fails."""
    expander.skip_whitespace()
    counter_name = None
    if brackets:
        counter_name = expander.parse_bracket_as_tokens()
    else:
        counter_name = expander.parse_brace_as_tokens()
    if counter_name is None:
        return None

    counter_name = expander.convert_tokens_to_str(counter_name)
    return f"c@{counter_name}"


def _parse_counter_args(
    expander: ExpanderCore, command_name: str
) -> Optional[Tuple[str, int]]:
    """Parse counter name and value arguments for counter-related commands.
    Returns tuple of (register_name, value) or None if parsing fails."""
    register_name = _parse_counter_name(expander)
    if register_name is None:
        expander.logger.warning(rf"\{command_name}: Missing counter name argument")
        return None

    # Get the value argument
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens()
    if value is None:
        expander.logger.warning(rf"\{command_name}: Missing or invalid value argument")
        return None

    value = int(expander.convert_tokens_to_str(value))
    return register_name, value


def setcounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \setcounter{counter_name}{value}"""
    result = _parse_counter_args(expander, "setcounter")
    if result is None:
        return None

    register_name, value = result
    expander.set_register(RegisterType.COUNT, register_name, value, is_global=True)
    return []


def addtocounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \addtocounter{counter_name}{value}"""
    result = _parse_counter_args(expander, "addtocounter")
    if result is None:
        return None

    register_name, value = result
    expander.increment_register(RegisterType.COUNT, register_name, value)
    return []


def stepcounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \stepcounter{counter_name} - increments counter by 1"""
    register_name = _parse_counter_name(expander)
    if register_name is None:
        expander.logger.warning(rf"\{token.value}: Missing counter name argument")
        return None

    expander.increment_register(RegisterType.COUNT, register_name, 1)
    return []


def value_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \value{counter_name} - returns the current value of the counter"""
    register_name = _parse_counter_name(expander)
    if register_name is None:
        expander.logger.warning(r"\value: Missing counter name argument")
        return None

    return expander.get_register_value_as_tokens(
        RegisterType.COUNT, register_name, return_default=True
    )


def newcounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \newcounter{counter_name} - creates a new counter"""
    register_name = _parse_counter_name(expander)
    if register_name is None:
        expander.logger.warning(r"\newcounter: Missing counter name argument")
        return None

    expander.set_register(RegisterType.COUNT, register_name, 0, is_global=True)

    def the_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
        return expander.get_register_value_as_tokens(
            RegisterType.COUNT, register_name, return_default=True
        )

    # creates \the{counter_name} handler e.g. \thesection
    base_name = register_name.split("@")[1]  # c@section -> section
    expander.register_handler("the" + base_name, the_handler, is_global=True)

    # check optional bracket [parent] arg
    parent_name = _parse_counter_name(expander, brackets=True)
    if parent_name:
        pass

    return []


def register_counter_handlers(expander: ExpanderCore):
    expander.register_macro(
        "setcounter",
        Macro("setcounter", setcounter_handler, []),
        is_global=True,
    )
    expander.register_macro(
        "addtocounter",
        Macro("addtocounter", addtocounter_handler, []),
        is_global=True,
    )
    expander.register_macro(
        "stepcounter",
        Macro("stepcounter", stepcounter_handler, []),
        is_global=True,
    )
    expander.register_macro(
        "refstepcounter",
        # make it the same as step counter, we handle labels/refs separately
        Macro("refstepcounter", stepcounter_handler, []),
        is_global=True,
    )
    expander.register_macro(
        "value",
        Macro("value", value_handler, []),
        is_global=True,
    )

    # new counter
    expander.register_macro(
        "newcounter",
        Macro("newcounter", newcounter_handler, []),
        is_global=True,
    )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_counter_handlers(expander)

    # all counter ops are global
    expander.push_scope()
    expander.expand(r"\setcounter{section}{10}")
    expander.expand(r"\addtocounter{section} {5}")  # section will be 15 after this
    expander.expand(r"\stepcounter {section}")  # section will be 16 after this
    expander.expand(r"\refstepcounter{section}")  # section will be 17 after this
    expander.pop_scope()

    out = expander.expand(r"\the\value{section}")

    expander.expand(r"\newcounter {mysection}[section] \stepcounter{mysection}")
    out = expander.expand(r"\themysection")

    # test return 0 by default if value not exist
    expander.expand(r"\the\value{se22ctionsss}")
