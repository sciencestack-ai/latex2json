from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Union, List

from latex2json.tokens.types import Token, TokenType
from latex2json.registers.utils import int_to_roman, int_to_alpha
from latex2json.tokens.utils import wrap_tokens_in_braces


class RegisterType(Enum):
    COUNT = "count"
    DIMEN = "dimen"
    SKIP = "skip"
    MUSKIP = "muskip"
    TOKS = "toks"
    BOX = "box"
    BOOL = "bool"
    INSERT = "insert"
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
            RegisterType.INSERT,
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
    content: List[Token] = field(default_factory=list)
    args: Optional[List[List[Token]]] = None
    width: int = 0  # Width in scaled points
    height: int = 0  # Height in scaled points
    depth: int = 0  # Depth in scaled points

    def to_tokens(self, content_only=True) -> List[Token]:
        if not self.content:
            return []
        if content_only:
            return self.content.copy()

        # return the full box command with args + content
        box_cmd = self.type.lstrip("\\")
        out_tokens = [
            Token(type=TokenType.CONTROL_SEQUENCE, value=box_cmd)
        ]  # e.g \hbox
        if self.args:
            for arg in self.args:
                out_tokens += wrap_tokens_in_braces(arg.copy())
        out_tokens += wrap_tokens_in_braces(self.content.copy())
        return out_tokens
