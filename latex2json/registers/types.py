from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union, List

from latex2json.tokens.types import Token
from latex2json.registers.utils import int_to_roman, int_to_alpha


class RegisterType(Enum):
    COUNT = "count"
    DIMEN = "dimen"
    SKIP = "skip"
    MUSKIP = "muskip"
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
        if self in [
            RegisterType.COUNT,
            RegisterType.DIMEN,
            RegisterType.SKIP,
            RegisterType.MUSKIP,
        ]:
            return 0
        elif self == RegisterType.TOKS:
            return []
        elif self == RegisterType.BOX:
            return Box()
        elif self == RegisterType.BOOL:
            return False
        else:
            return None


class CounterFormat(Enum):
    """Enum for counter formatting styles"""

    ARABIC = "arabic"  # 1, 2, 3
    ROMAN = "roman"  # i, ii, iii
    ROMAN_UPPER = "Roman"  # I, II, III
    ALPHA = "alph"  # a, b, c
    ALPHA_UPPER = "Alph"  # A, B, C

    def __str__(self):
        return self.value

    @classmethod
    def from_str(cls, value: Union[str, "CounterFormat"]) -> "CounterFormat":
        """Convert string to CounterFormat if needed"""
        if isinstance(value, cls):
            return value
        try:
            return cls(value)
        except ValueError:
            return cls.ARABIC

    def format_value(self, value: int) -> str:
        """Format an integer value according to this format style"""
        match self:
            case CounterFormat.ARABIC:
                return str(value)
            case CounterFormat.ROMAN:
                return int_to_roman(value, lowercase=True)
            case CounterFormat.ROMAN_UPPER:
                return int_to_roman(value, lowercase=False)
            case CounterFormat.ALPHA:
                return int_to_alpha(value, lowercase=True)
            case CounterFormat.ALPHA_UPPER:
                return int_to_alpha(value, lowercase=False)


@dataclass
class Box:
    """Represents a TeX box with content and dimensions"""

    type: str = "hbox"
    content: List[Token] = field(
        default_factory=list
    )  # Forward reference for Token type
    width: int = 0  # Width in scaled points
    height: int = 0  # Height in scaled points
    depth: int = 0  # Depth in scaled points

    def to_tokens(self) -> List[Token]:
        return self.content.copy()
