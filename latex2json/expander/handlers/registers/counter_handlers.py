from typing import List, Optional, Tuple
from latex2json.expander.macro_registry import Macro
from latex2json.tokens import Token
from latex2json.expander.expander_core import ExpanderCore


def parse_counter_name(expander: ExpanderCore, brackets=False) -> Optional[str]:
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
    return counter_name.strip()


def parse_counter_args(
    expander: ExpanderCore, command_name: str
) -> Optional[Tuple[str, int]]:
    """Parse counter name and value arguments for counter-related commands.
    Returns tuple of (counter_name, value) or None if parsing fails."""
    counter_name = parse_counter_name(expander)
    if not counter_name:
        expander.logger.warning(rf"\{command_name}: Missing counter name argument")
        return None

    # Get the value argument
    expander.skip_whitespace()
    value = expander.parse_brace_as_tokens()
    if value is None:
        expander.logger.warning(rf"\{command_name}: Missing or invalid value argument")
        return None

    value = expander.convert_tokens_to_str(value)
    return counter_name, value


def setcounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \setcounter{counter_name}{value}"""
    result = parse_counter_args(expander, "setcounter")
    if result is None:
        return None

    counter_name, value = result
    expander.state.set_counter(counter_name, int(value))
    return []


def addtocounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \addtocounter{counter_name}{value}"""
    result = parse_counter_args(expander, "addtocounter")
    if result is None:
        return None

    counter_name, value = result
    expander.state.add_to_counter(counter_name, int(value))
    return []


def stepcounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \stepcounter{counter_name} - increments counter by 1"""
    counter_name = parse_counter_name(expander)
    if not counter_name:
        expander.logger.warning(rf"\{token.value}: Missing counter name argument")
        return None

    expander.state.step_counter(counter_name)
    return []


def get_counter_value_as_tokens(
    expander: ExpanderCore, counter_name: str
) -> Optional[List[Token]]:
    value = expander.state.get_counter_as_format(counter_name)
    if value is None:
        return None
    return expander.convert_str_to_tokens(str(value))


def value_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \value{counter_name} - returns the current value of the counter"""
    counter_name = parse_counter_name(expander)
    if not counter_name:
        expander.logger.warning(r"\value: Missing counter name argument")
        return None

    return get_counter_value_as_tokens(expander, counter_name)


def newcounter_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handle \newcounter{counter_name} - creates a new counter"""
    counter_name = parse_counter_name(expander)
    if not counter_name:
        expander.logger.warning(r"\newcounter: Missing counter name argument")
        return None

    # check optional bracket [parent] arg
    parent_name = parse_counter_name(expander, brackets=True)
    expander.create_new_counter(counter_name, parent_name)

    return []


def counterwithin_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    r"""Handle \counterwithin{counter_name}{parent_counter_name} - sets the counter to be within the parent counter"""
    result = parse_counter_args(expander, "counterwithin")
    if result is None:
        return None

    counter_name, parent_name = result
    expander.state.counter_within(counter_name, parent_name)
    return []


def counterwithout_handler(
    expander: ExpanderCore, token: Token
) -> Optional[List[Token]]:
    result = parse_counter_args(expander, "counterwithout")
    if result is None:
        return None

    counter_name, parent_name = result
    expander.state.counter_within(counter_name, None)
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

    expander.register_macro(
        "counterwithin",
        Macro("counterwithin", counterwithin_handler, []),
        is_global=True,
    )
    expander.register_macro(
        "counterwithout",
        Macro("counterwithout", counterwithout_handler, []),
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
    expander.expand(r"\setcounter{mysection}{10}")
    # test that mysection counter is 10
    out = expander.expand(r"\themysection")  # 10
    # check stepcounter section
    expander.expand(r"\stepcounter{section}")
    out = expander.expand(r"\thesection")  # 17
    # check that mysection is reset
    out = expander.expand(r"\themysection")  # 0

    # test return 0 by default if value not exist
    expander.expand(r"\the\value{se22ctionsss}")
