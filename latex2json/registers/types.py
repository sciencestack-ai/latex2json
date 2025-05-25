from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Union, List

from latex2json.tokens.types import Token
from latex2json.registers.utils import int_to_roman, int_to_alpha


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
