from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro
from latex2json.registers import RegisterType
from latex2json.tokens.types import Token, TokenType


def get_newif_register_value(expander: ExpanderCore, name: str) -> bool:
    value = expander.get_register_value(RegisterType.BOOL, name)
    if value is None:
        return False
    return value


def evaluate_newif_condition(
    expander: ExpanderCore, token: Token
) -> tuple[bool | None, str | None]:
    # Get the macro that stores the condition state
    condition_macro = expander.get_macro(token)

    if not isinstance(condition_macro, IfMacro):
        return None, f"Condition {token.value} is not a valid IfMacro"

    return get_newif_register_value(expander, token.value), None


def register_newif_name_macros(expander: ExpanderCore, name: str, is_user_defined=True):
    r"""
    Where name is the name of the newif, e.g. "cool"
    """
    ifname = "if" + name
    # Create the condition macro
    condition = IfMacro(ifname, evaluate_newif_condition)
    expander.register_macro(
        ifname, condition, is_global=True, is_user_defined=is_user_defined
    )

    # Create the true/false setters
    def create_bool_setter(value: bool):
        def set_bool_handler(
            expander: ExpanderCore, token: Token
        ) -> Optional[List[Token]]:
            expander.set_register(RegisterType.BOOL, ifname, value, is_global=True)
            return []

        return set_bool_handler

    true_setter = create_bool_setter(True)
    false_setter = create_bool_setter(False)
    false_setter(expander, None)  # set false by default

    # Register the setters
    expander.register_handler(name + "true", true_setter, is_global=True)
    expander.register_handler(name + "false", false_setter, is_global=True)


def newif_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    r"""Handles \newif command which creates a new if condition.
    Format: \newif\ifname
    Creates:
    - \ifname (the condition)
    - \namefalse (sets condition to false)
    - \nametrue (sets condition to true)
    """
    expander.skip_whitespace()
    name_token = expander.consume()
    if name_token is None:
        expander.logger.warning("\\newif expects a name")
        return None

    if name_token.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning("\\newif name must be a control sequence")
        return None

    # Name must start with \if
    ifname = name_token.value
    if not ifname.startswith("if"):
        expander.logger.warning("\\newif name must start with \\if")
        return None

    base_name = ifname[2:]
    if base_name == "":
        expander.logger.warning("\\newif name cannot be single \\if")
        return None

    register_newif_name_macros(expander, base_name)

    return []


def register_newif(expander: ExpanderCore):
    expander.register_handler("\\newif", newif_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander
    from latex2json.tokens.utils import strip_whitespace_tokens

    expander = Expander()
    text = r"""
\newif\ifcool
\cooltrue

\ifnum\ifcool 1 \else 0 \fi>0
  Cool is true
\else
  Cool is false
\fi
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    print(out)
