from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Tuple, Union, List

from latex2json.expander.macro_registry import Handler, Macro
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.tokens import Token
from latex2json.tokens.types import TokenType

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore


class RegisterType(Enum):
    COUNT = "count"
    DIMEN = "dimen"
    SKIP = "skip"
    TOKS = "toks"
    BOX = "box"
    OTHER = "other"

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value: Union[str, "RegisterType"]) -> "RegisterType":
        """Convert string to RegisterType if needed"""
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            return cls.OTHER


def get_register_handler(
    expander: "ExpanderCore", token: Token
) -> Optional[Tuple[RegisterType, Union[int, str]]]:
    macro = expander.get_macro(token.value)
    if isinstance(macro, RegisterMacro):
        if expander.peek() == token:
            expander.consume()
        register_type = macro.register_type
        reg_id = macro.name

        if not macro.is_named:
            if register_type == RegisterType.OTHER:
                raise NotImplementedError(
                    f"Getting register:{register_type} is not implemented"
                )
            else:
                tok = expander.peek()
                reg_id = expander.parse_integer()
                if reg_id is None:
                    expander.logger.warning(
                        f"Register:{register_type} invalid register id, tok: {tok}"
                    )
                    return None
        return register_type, reg_id
    return None


def parse_registertype_value(
    expander: "ExpanderCore", register_type: RegisterType
) -> Optional[int]:
    value = None
    if register_type == RegisterType.COUNT:
        return expander.parse_integer()
    elif register_type == RegisterType.DIMEN:
        value = expander.parse_dimensions()
        if value:
            value = dimension_to_scaled_points(value[0], value[1])
    else:
        raise NotImplementedError(f"Setting {register_type} is not implemented")

    return value


def set_register_value_handler(
    expander: "ExpanderCore",
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
    expander: "ExpanderCore",
    token: Token,
    is_named_register: bool = False,
) -> Optional[List[Token]]:
    parsed = get_register_handler(expander, token)
    if not parsed:
        return [token]
    register_type, reg_id = parsed
    if set_register_value_handler(expander, register_type, reg_id):
        return []
    # don't expand by default # expander.get_register_value_as_tokens(register_type, reg_id)
    # return the token itself instead since it is technically non-expandable
    if not is_named_register:
        return [token] + expander.convert_str_to_tokens(str(reg_id))
    return [token]


class RegisterMacro(Macro):
    def __init__(self, register_type: RegisterType, command_name: str, is_named=False):
        handler: Handler = lambda expander, token: registertype_macro_handler(
            expander, token, is_named
        )
        super().__init__(command_name, handler, [])
        self.register_type = register_type
        self.is_named = is_named


class NewRegisterMacro(Macro):
    def __init__(self, register_type: RegisterType, command_name: str):

        handler: Handler = lambda expander, token: new_register_macro_handler(
            expander, token, register_type
        )
        super().__init__(command_name, handler, [])
        self.register_type = register_type


def new_register_macro_handler(
    expander: "ExpanderCore",
    token: Token,
    register_type: RegisterType,
) -> Optional[List[Token]]:
    tok = expander.peek()
    if tok is None or tok.type != TokenType.CONTROL_SEQUENCE:
        expander.logger.warning(f"Warning: \\newcount expects a \name, but found {tok}")
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

    expander.create_register(register_type, count_name, default_value, is_global=True)

    return []


def register_all_register_macros(expander: "ExpanderCore"):
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


@dataclass
class Glue:
    """Represents TeX glue with natural width and stretch/shrink components"""

    width: int  # Natural width in scaled points
    stretch: int  # Stretch amount in scaled points
    shrink: int  # Shrink amount in scaled points


@dataclass
class Box:
    """Represents a TeX box with content and dimensions"""

    content: List[Token]  # Forward reference for Token type
    width: int  # Width in scaled points
    height: int  # Height in scaled points
    depth: int  # Depth in scaled points


class TexRegisters:
    """Manages TeX registers including counts, dimensions, skips, tokens, and boxes"""

    def __init__(self):
        # Internal storage, organized by type
        self._counts: list[int] = [0] * 256
        self._dimens_sp: list[int] = [
            0
        ] * 256  # Dimensions stored as scaled points (int)
        self._skips: list[Glue] = [Glue(0, 0, 0)] * 256
        self._toks: list[list[Token]] = [[] for _ in range(256)]
        self._boxes: list[Optional[Box]] = [None] * 256

        # For named registers (e.g., \newcount\mycounter)
        self._named_counts: dict[str, int] = {}
        self._named_dimens_sp: dict[str, int] = {}
        self._named_skips: dict[str, Glue] = {}
        self._named_toks: dict[str, list[Token]] = {}
        self._named_boxes: dict[str, Optional[Box]] = {}

        # A mapping for quick lookup in generic internal helpers
        self._register_pools = {
            RegisterType.COUNT: self._counts,
            RegisterType.DIMEN: self._dimens_sp,
            RegisterType.SKIP: self._skips,
            RegisterType.TOKS: self._toks,
            RegisterType.BOX: self._boxes,
        }
        self._named_register_pools = {
            RegisterType.COUNT: self._named_counts,
            RegisterType.DIMEN: self._named_dimens_sp,
            RegisterType.SKIP: self._named_skips,
            RegisterType.TOKS: self._named_toks,
            RegisterType.BOX: self._named_boxes,
        }

    def get_count(self, reg_id: Union[int, str]) -> int:
        """Get the value of a count register"""
        return self._get_generic_register(RegisterType.COUNT, reg_id)

    def set_count(self, reg_id: Union[int, str], value: int) -> None:
        """Set the value of a count register"""
        self._set_generic_register(RegisterType.COUNT, reg_id, value)

    def get_dimen(self, reg_id: Union[int, str]) -> int:
        """Get the value of a dimension register in scaled points"""
        return self._get_generic_register(RegisterType.DIMEN, reg_id)

    def set_dimen(self, reg_id: Union[int, str], value: int) -> None:
        """Set the value of a dimension register in scaled points"""
        self._set_generic_register(RegisterType.DIMEN, reg_id, value)

    def get_skip(self, reg_id: Union[int, str]) -> Glue:
        """Get the value of a skip register"""
        return self._get_generic_register(RegisterType.SKIP, reg_id)

    def set_skip(self, reg_id: Union[int, str], value: Glue) -> None:
        """Set the value of a skip register"""
        self._set_generic_register(RegisterType.SKIP, reg_id, value)

    def get_toks(self, reg_id: Union[int, str]) -> List[Token]:
        """Get the value of a token register"""
        return self._get_generic_register(RegisterType.TOKS, reg_id)

    def set_toks(self, reg_id: Union[int, str], value: List[Token]) -> None:
        """Set the value of a token register"""
        self._set_generic_register(RegisterType.TOKS, reg_id, value)

    def get_box(self, reg_id: Union[int, str]) -> Optional[Box]:
        """Get the value of a box register"""
        return self._get_generic_register(RegisterType.BOX, reg_id)

    def set_box(self, reg_id: Union[int, str], value: Optional[Box]) -> None:
        """Set the value of a box register"""
        self._set_generic_register(RegisterType.BOX, reg_id, value)

    def get_register(self, reg_type: RegisterType, reg_id: Union[int, str]):
        return self._get_generic_register(reg_type, reg_id)

    def set_register(self, reg_type: RegisterType, reg_id: Union[int, str], value: Any):
        self._set_generic_register(reg_type, reg_id, value)

    def delete_register(self, reg_type: RegisterType, reg_id: str):
        if reg_id in self._named_register_pools.get(reg_type, {}):
            del self._named_register_pools[reg_type][reg_id]

    def _get_generic_register(
        self, reg_type: Union[str, RegisterType], reg_id: Union[int, str]
    ):
        """Internal helper to get register value by type and ID"""
        reg_type = RegisterType.from_str(reg_type)
        if isinstance(reg_id, str) and reg_id.isdigit():
            reg_id = int(reg_id)
        if isinstance(reg_id, int):
            if not 0 <= reg_id < 256:
                return None
            return self._register_pools[reg_type][reg_id]
        elif isinstance(reg_id, str):
            try:
                return self._named_register_pools[reg_type][reg_id]
            except KeyError:
                return None
        return None

    def _set_generic_register(
        self, reg_type: Union[str, RegisterType], reg_id: Union[int, str], value: Any
    ) -> None:
        """Internal helper to set register value by type and ID"""
        reg_type = RegisterType.from_str(reg_type)
        if isinstance(reg_id, str) and reg_id.isdigit():
            reg_id = int(reg_id)
        if isinstance(reg_id, int):
            if not 0 <= reg_id < 256:
                return None
            self._register_pools[reg_type][reg_id] = value
        elif isinstance(reg_id, str):
            self._named_register_pools[reg_type][reg_id] = value
        return None


if __name__ == "__main__":
    reg = TexRegisters()
    reg.set_register(RegisterType.COUNT, "newcounter", 0)
    print(reg.get_count(0))
    reg.delete_register(RegisterType.COUNT, "newcounter")
    print(reg.get_count(0))
