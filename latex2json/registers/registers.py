from typing import Any, Optional, Union
from latex2json.registers.types import Box, RegisterType
from latex2json.tokens.types import Token


BUILTIN_DIMENSIONS = [
    # Page dimensions
    "textwidth",  # Width of text area
    "textheight",  # Height of text area
    "paperwidth",  # Total page width
    "paperheight",  # Total page height
    # Paragraph formatting
    "parindent",  # Paragraph indentation
    "parskip",  # Space between paragraphs
    "baselineskip",  # Space between lines
    # List formatting
    "leftmargin",  # Left margin in lists
    "rightmargin",  # Right margin in lists
    "itemsep",  # Space between list items
]


class TexRegisters:
    """Manages TeX registers including counts, dimensions, skips, tokens, and boxes"""

    def __init__(self):
        # Internal storage, organized by type
        self._counts: list[int] = [0] * 256
        self._dimens_sp: list[int] = [
            0
        ] * 256  # Dimensions stored as scaled points (int)
        self._skips: list[int] = [0] * 256  # Skip stored as scaled points (int)
        self._muskips: list[int] = [0] * 256  # Math skip stored as scaled points (int)

        self._toks: list[list[Token]] = [[] for _ in range(256)]
        self._boxes: list[Optional[Box]] = [None] * 256

        # For named registers (e.g., \newcount\mycounter)
        self._named_counts: dict[str, int] = {}
        self._named_dimens_sp: dict[str, int] = {}
        self._named_skips: dict[str, int] = {}
        self._named_muskips: dict[str, int] = {}
        self._named_toks: dict[str, list[Token]] = {}
        self._named_boxes: dict[str, Optional[Box]] = {}
        self._named_bools: dict[str, bool] = {}

        # A mapping for quick lookup in generic internal helpers
        self._register_pools = {
            RegisterType.COUNT: self._counts,
            RegisterType.DIMEN: self._dimens_sp,
            RegisterType.SKIP: self._skips,
            RegisterType.MUSKIP: self._muskips,
            RegisterType.TOKS: self._toks,
            RegisterType.BOX: self._boxes,
        }
        self._named_register_pools = {
            RegisterType.COUNT: self._named_counts,
            RegisterType.DIMEN: self._named_dimens_sp,
            RegisterType.SKIP: self._named_skips,
            RegisterType.MUSKIP: self._named_muskips,
            RegisterType.TOKS: self._named_toks,
            RegisterType.BOX: self._named_boxes,
            RegisterType.BOOL: self._named_bools,
        }

        self._init_builtin_registers()

    def _init_builtin_registers(self):
        for dimen in BUILTIN_DIMENSIONS:
            self.set_register(RegisterType.DIMEN, dimen, 0)

    def get_register_value(self, reg_type: RegisterType, reg_id: Union[int, str]):
        out = self._get_generic_register_value(reg_type, reg_id)
        if reg_type == RegisterType.BOX and isinstance(out, Box):
            out.width = (
                self._get_generic_register_value(RegisterType.DIMEN, f"wd{reg_id}") or 0
            )
            out.height = (
                self._get_generic_register_value(RegisterType.DIMEN, f"ht{reg_id}") or 0
            )
            out.depth = (
                self._get_generic_register_value(RegisterType.DIMEN, f"dp{reg_id}") or 0
            )
        return out

    def set_register(self, reg_type: RegisterType, reg_id: Union[int, str], value: Any):
        self._set_generic_register(reg_type, reg_id, value)
        if reg_type == RegisterType.BOX and isinstance(value, Box):
            self._set_generic_register(RegisterType.DIMEN, f"wd{reg_id}", value.width)
            self._set_generic_register(RegisterType.DIMEN, f"ht{reg_id}", value.height)
            self._set_generic_register(RegisterType.DIMEN, f"dp{reg_id}", value.depth)

    def create_register(
        self, reg_type: RegisterType, reg_id: str, default_value: Optional[Any] = None
    ):
        if default_value is None:
            default_value = reg_type.get_default_value()
        self._set_generic_register(reg_type, reg_id, default_value)

    def delete_register(self, reg_type: RegisterType, reg_id: str):
        if reg_id in self._named_register_pools.get(reg_type, {}):
            del self._named_register_pools[reg_type][reg_id]

    def get_register_pools(self):
        return {"base": self._register_pools, "named": self._named_register_pools}

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
        else:
            raise NotImplementedError(f"Incrementing {reg_type} is not implemented")
            # Other register types don't support increment operations
            return None

        self.set_register(reg_type, reg_id, new_value)


if __name__ == "__main__":
    reg = TexRegisters()
    reg.set_register(RegisterType.COUNT, "newcounter", 0)
