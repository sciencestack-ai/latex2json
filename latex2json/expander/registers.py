from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Optional, Union, List

from latex2json.tokens import Token


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
            "count": self._counts,
            "dimen": self._dimens_sp,
            "skip": self._skips,
            "toks": self._toks,
            "box": self._boxes,
        }
        self._named_register_pools = {
            "count": self._named_counts,
            "dimen": self._named_dimens_sp,
            "skip": self._named_skips,
            "toks": self._named_toks,
            "box": self._named_boxes,
        }

    def get_count(self, reg_id: Union[int, str]) -> int:
        """Get the value of a count register"""
        return self._get_generic_register("count", reg_id)

    def set_count(self, reg_id: Union[int, str], value: int) -> None:
        """Set the value of a count register"""
        self._set_generic_register("count", reg_id, value)

    def get_dimen(self, reg_id: Union[int, str]) -> int:
        """Get the value of a dimension register in scaled points"""
        return self._get_generic_register("dimen", reg_id)

    def set_dimen(self, reg_id: Union[int, str], value: int) -> None:
        """Set the value of a dimension register in scaled points"""
        self._set_generic_register("dimen", reg_id, value)

    def get_skip(self, reg_id: Union[int, str]) -> Glue:
        """Get the value of a skip register"""
        return self._get_generic_register("skip", reg_id)

    def set_skip(self, reg_id: Union[int, str], value: Glue) -> None:
        """Set the value of a skip register"""
        self._set_generic_register("skip", reg_id, value)

    def get_toks(self, reg_id: Union[int, str]) -> List[Token]:
        """Get the value of a token register"""
        return self._get_generic_register("toks", reg_id)

    def set_toks(self, reg_id: Union[int, str], value: List[Token]) -> None:
        """Set the value of a token register"""
        self._set_generic_register("toks", reg_id, value)

    def get_box(self, reg_id: Union[int, str]) -> Optional[Box]:
        """Get the value of a box register"""
        return self._get_generic_register("box", reg_id)

    def set_box(self, reg_id: Union[int, str], value: Optional[Box]) -> None:
        """Set the value of a box register"""
        self._set_generic_register("box", reg_id, value)

    def get_register(self, reg_name: str, reg_id: Union[int, str]):
        return self._get_generic_register(reg_name, reg_id)

    def set_register(self, reg_name: str, reg_id: Union[int, str], value: Any):
        self._set_generic_register(reg_name, reg_id, value)

    def _get_generic_register(self, reg_name: str, reg_id: Union[int, str]):
        """Internal helper to get register value by type and ID"""
        if isinstance(reg_id, int):
            if not 0 <= reg_id < 256:
                return None
            return self._register_pools[reg_name][reg_id]
        elif isinstance(reg_id, str):
            try:
                return self._named_register_pools[reg_name][reg_id]
            except KeyError:
                return None
        return None

    def _set_generic_register(
        self, reg_type_str: str, reg_id: Union[int, str], value: Any
    ) -> None:
        """Internal helper to set register value by type and ID"""
        if isinstance(reg_id, int):
            if not 0 <= reg_id < 256:
                return None
            self._register_pools[reg_type_str][reg_id] = value
        elif isinstance(reg_id, str):
            self._named_register_pools[reg_type_str][reg_id] = value
        return None

    def copy(self):
        """Copy the state manager"""
        return deepcopy(self)
