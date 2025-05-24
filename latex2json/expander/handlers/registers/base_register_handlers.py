from typing import Tuple, Optional, List, Union
from latex2json.expander.macro_registry import Handler, Macro, MacroType
from latex2json.expander.registers import Glue, RegisterType, parse_registertype_value
from latex2json.tokens import Token
from latex2json.tokens.types import TokenType

from latex2json.expander.expander_core import ExpanderCore


def get_register_handler(
    expander: ExpanderCore, token: Token
) -> Optional[Tuple[RegisterType, Union[int, str]]]:
    macro = expander.get_macro(token.value)
    if isinstance(macro, RegisterMacro):
        if expander.peek() == token:
            expander.consume()
        register_type = macro.register_type
        reg_id = macro.name

        if macro.is_primitive:
            if register_type == RegisterType.OTHER:
                raise NotImplementedError(
                    f"Getting register:{register_type} is not implemented"
                )

            # detect primitive register id e.g. \count100 -> 100
            tok = expander.peek()
            reg_id = expander.parse_integer()
            if reg_id is None:
                expander.logger.warning(
                    f"Register:{register_type} invalid register id, tok: {tok}"
                )
                return None
        return register_type, reg_id
    return None


def set_register_value_handler(
    expander: ExpanderCore,
    register_type: RegisterType,
    reg_id: Union[int, str],
    check_equals=True,
) -> bool:
    if check_equals and not expander.parse_equals():
        return False

    # if = is found, it's an assignment
    expander.skip_whitespace()
    value = parse_registertype_value(expander, register_type)

    if value is None:
        expander.logger.warning(
            f"Register:{register_type} invalid = assignment, tok: {expander.peek()}"
        )
        return False
    expander.set_register(register_type, reg_id, value)
    return True


def registertype_macro_handler(
    expander: ExpanderCore,
    token: Token,
    is_primitive_register: bool = True,
) -> Optional[List[Token]]:
    parsed = get_register_handler(expander, token)
    if not parsed:
        return [token]
    register_type, reg_id = parsed
    if set_register_value_handler(expander, register_type, reg_id):
        return []
    # don't expand by default # expander.get_register_value_as_tokens(register_type, reg_id)
    # return the token itself instead since it is technically non-expandable
    if is_primitive_register:
        # e.g. \count20 -> [\count, 2, 0]
        return [token] + expander.convert_str_to_tokens(str(reg_id))
    return [token]


class RegisterMacro(Macro):
    def __init__(
        self, register_type: RegisterType, command_name: str, is_primitive=True
    ):
        handler: Handler = lambda expander, token: registertype_macro_handler(
            expander, token, is_primitive
        )
        super().__init__(command_name, handler, [], type=MacroType.REGISTER)
        self.register_type = register_type
        self.is_primitive = is_primitive


class NewRegisterMacro(Macro):
    def __init__(self, register_type: RegisterType, command_name: str):

        handler: Handler = lambda expander, token: new_register_macro_handler(
            expander, token, register_type
        )
        super().__init__(command_name, handler, [])
        self.register_type = register_type


def new_register_macro_handler(
    expander: ExpanderCore,
    token: Token,
    register_type: RegisterType,
) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(
            f"Warning: \\new{register_type.value} expects a \\name, but found {tok}"
        )
        return None
    count_name = tok.value
    expander.consume()

    default_value = 0
    if register_type == RegisterType.SKIP:
        default_value = Glue(0, 0, 0)
    elif register_type == RegisterType.BOX:
        default_value = None  # Box([])
    elif register_type == RegisterType.TOKS:
        default_value = []
    elif register_type == RegisterType.BOOL:
        default_value = False

    expander.set_register(register_type, count_name, default_value, is_global=True)
    # create a macro for the register
    expander.register_macro(
        count_name,
        RegisterMacro(register_type, count_name, is_primitive=False),
        is_global=True,
    )

    return []


def register_base_register_macros(expander: ExpanderCore):
    for register_type in RegisterType:
        cmd_name = register_type.value
        expander.register_macro(
            cmd_name,
            RegisterMacro(register_type, cmd_name),
            is_global=True,
        )

        new_register_name = f"new{cmd_name}"
        expander.register_macro(
            new_register_name,
            NewRegisterMacro(register_type, new_register_name),
            is_global=True,
        )
