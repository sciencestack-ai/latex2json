from typing import Tuple, Optional, List, Union
from latex2json.expander.macro_registry import Handler, Macro, MacroType
from latex2json.registers import RegisterType
from latex2json.registers.registers import BUILTIN_DIMENSIONS
from latex2json.tokens import Token
from latex2json.tokens.types import TokenType

from latex2json.expander.expander_core import ExpanderCore


def parse_register_setter(
    expander: ExpanderCore, register_type: RegisterType
) -> Optional[int | List[Token]]:
    value = None
    expander.skip_whitespace()
    if register_type == RegisterType.COUNT:
        return expander.parse_integer()
    elif register_type == RegisterType.DIMEN:
        return expander.parse_dimensions()
    elif register_type == RegisterType.BOX:
        return expander.parse_box()
    elif register_type == RegisterType.TOKS:
        return expander.parse_brace_as_tokens()
    elif register_type in [RegisterType.SKIP, RegisterType.MUSKIP]:
        return expander.parse_skip()
    else:
        raise NotImplementedError(f"Setting {register_type} is not implemented")

    return value


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
    value = parse_register_setter(expander, register_type)

    if value is None:
        expander.logger.warning(
            f"Register:{register_type} invalid = assignment, tok: {expander.peek()}"
        )
        return False
    expander.set_register(register_type, reg_id, value)
    return True


def make_primitive_register_handler(is_id_integer: bool = True) -> Handler:
    def primitive_register_handler(
        expander: ExpanderCore, token: Token
    ) -> Optional[List[Token]]:
        macro = expander.get_macro(token.value)
        if not macro or not isinstance(macro, RegisterMacro):
            return [token]

        register_type, reg_id = macro.parse_register(expander, token)
        if reg_id is None:
            return [token]

        if set_register_value_handler(expander, register_type, reg_id):
            return []

        if is_id_integer:
            # e.g. \count20 -> [\count, 2, 0]
            return [token] + expander.convert_str_to_tokens(str(reg_id))
        return [token]

    return primitive_register_handler


class RegisterMacro(Macro):
    def __init__(
        self,
        register_type: RegisterType,
        command_name: str,
        handler: Handler,
        is_id_integer: bool = True,
    ):
        super().__init__(command_name, handler, [], type=MacroType.REGISTER)
        self.command_name = command_name
        self.register_type = register_type
        self.is_id_integer = is_id_integer
        self.parse_register = self._parse_register

    def _parse_register(
        self, expander: ExpanderCore, token: Token
    ) -> Tuple[RegisterType, Optional[Union[int, str]]]:
        if expander.peek() == token:
            expander.consume()

        reg_id: Optional[Union[int, str]] = None
        if self.is_id_integer:
            # detect primitive register id e.g. \count100 -> 100
            reg_id = expander.parse_integer()
            if reg_id is None:
                expander.logger.warning(
                    f"Register:{self.register_type} invalid register id, tok: {expander.peek()}"
                )
                return self.register_type, None
        else:
            reg_id = self.command_name

        return self.register_type, reg_id


def make_register_macro(
    register_type: RegisterType, command_name: str, is_id_integer: bool = True
) -> RegisterMacro:
    handler = make_primitive_register_handler(is_id_integer)
    return RegisterMacro(register_type, command_name, handler, is_id_integer)


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

    expander.state.create_register(register_type, count_name)
    # create a macro for the register
    expander.register_macro(
        count_name,
        make_register_macro(register_type, count_name, is_id_integer=False),
        is_global=True,
    )

    return []


def register_base_register_macros(expander: ExpanderCore):
    for register_type in RegisterType:
        if register_type == RegisterType.BOX or register_type == RegisterType.BOOL:
            # NOTE THAT \box is different since it requires \setbox. Handle it in box_handlers.py
            continue

        cmd_name = register_type.value

        # newcount/newdimen/newskip/newtoks/newbool
        new_register_name = f"new{cmd_name}"
        expander.register_macro(
            new_register_name,
            Macro(
                new_register_name,
                lambda e, t, rt=register_type: new_register_macro_handler(e, t, rt),
                [],
            ),
            is_global=True,
        )

        # SETTERS: count0/dimen0/skip0/toks0/bool0
        expander.register_macro(
            cmd_name,
            make_register_macro(register_type, cmd_name),
            is_global=True,
        )

    # textwidth/textheight/parindent/parskip etc
    for builtin_dimen in BUILTIN_DIMENSIONS:
        expander.register_macro(
            builtin_dimen,
            make_register_macro(RegisterType.DIMEN, builtin_dimen, is_id_integer=False),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    # test in scope
    text = r"""
        \newtoks\tokker
        \tokker={123}
        \the\tokker
    """.strip()
    expander.push_scope()
    out = expander.expand(text)
    expander.pop_scope()

    expander.state.get_register(RegisterType.TOKS, "tokker")
