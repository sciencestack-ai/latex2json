from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional, Union, List

from latex2json.tokens import Token

if TYPE_CHECKING:
    from latex2json.expander.expander_core import ExpanderCore


class RegisterType(Enum):
    COUNT = "count"
    DIMEN = "dimen"
    SKIP = "skip"
    TOKS = "toks"
    BOX = "box"
    BOOL = "bool"
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

    def get_default_value(self) -> Any:
        """Get the default value for this register type"""
        if self == RegisterType.COUNT:
            return 0
        elif self == RegisterType.DIMEN:
            return 0
        elif self == RegisterType.SKIP:
            return Glue(0, 0, 0)
        elif self == RegisterType.TOKS:
            return []
        elif self == RegisterType.BOX:
            return None
        elif self == RegisterType.BOOL:
            return False
        else:
            return None


def parse_registertype_value(
    expander: "ExpanderCore", register_type: RegisterType
) -> Optional[int]:
    value = None
    if register_type == RegisterType.COUNT:
        return expander.parse_integer()
    elif register_type == RegisterType.DIMEN:
        return expander.parse_dimensions()
    else:
        raise NotImplementedError(f"Setting {register_type} is not implemented")

    return value


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
        self._named_bools: dict[str, bool] = {}

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
            RegisterType.BOOL: self._named_bools,
        }

    def get_register_value(self, reg_type: RegisterType, reg_id: Union[int, str]):
        return self._get_generic_register_value(reg_type, reg_id)

    def set_register(self, reg_type: RegisterType, reg_id: Union[int, str], value: Any):
        self._set_generic_register(reg_type, reg_id, value)

    def delete_register(self, reg_type: RegisterType, reg_id: str):
        if reg_id in self._named_register_pools.get(reg_type, {}):
            del self._named_register_pools[reg_type][reg_id]

    def _get_generic_register_value(
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

    def increment_register(
        self, reg_type: RegisterType, reg_id: Union[int, str], increment: Any
    ) -> None:
        """Increment a register by the specified amount.

        Args:
            reg_type: Type of register (COUNT, DIMEN, etc.)
            reg_id: Register identifier (number or name)
            increment: Amount to increment by (type must match register type)
        """
        current_value = self.get_register_value(reg_type, reg_id)
        if current_value is None:
            current_value = reg_type.get_default_value()

        if reg_type in (RegisterType.COUNT, RegisterType.DIMEN):
            # For numeric registers, perform simple addition
            new_value = current_value + increment
        elif reg_type == RegisterType.SKIP:
            # For glue registers, add each component separately
            raise NotImplementedError(f"Incrementing {reg_type} is not implemented")
            # if not isinstance(increment, Glue):
            #     return None
            # new_value = Glue(
            #     width=current_value.width + increment.width,
            #     stretch=current_value.stretch + increment.stretch,
            #     shrink=current_value.shrink + increment.shrink,
            # )
        else:
            raise NotImplementedError(f"Incrementing {reg_type} is not implemented")
            # Other register types don't support increment operations
            return None

        self.set_register(reg_type, reg_id, new_value)


if __name__ == "__main__":
    reg = TexRegisters()
    reg.set_register(RegisterType.COUNT, "newcounter", 0)
