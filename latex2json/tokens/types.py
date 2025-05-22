from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Optional

from latex2json.tokens.catcodes import Catcode


# --- Define Token Types (based on Catcodes) ---
# These represent the fundamental types of tokens TeX produces based on catcodes.
# This enum is distinct from the Catcode enum, representing the *type* of token formed.
class TokenType(Enum):
    CONTROL_SEQUENCE = 1  # \command (name or symbol)
    CHARACTER = (
        2  # A character with a specific catcode (e.g., 'a' catcode 11, '{' catcode 1)
    )
    MATH_SHIFT = 3  # Simulate Catcode.Mathshift=3
    END_OF_LINE = 5  # Simulate Catcode.END_OF_LINE=5
    PARAMETER = 6  # Simulate Catcode.PARAMETER=6
    # Add other potential types if needed, though character/control sequence are primary
    # e.g., EndOfFile = 3, ParameterToken = 4 (for # in macro definitions)
    INVALID = 15  # For invalid tokens or errors


# --- Define the Token Class ---
# A token will store its type, value, and original position.
# For CHARACTER tokens, the value will be the character itself, and catcode is stored.
# For CONTROL_SEQUENCE tokens, the value will be the command name (e.g., "section"),
# and catcode is implicitly 0 (Escape) for the initial backslash.
class Token:
    def __init__(
        self,
        type: TokenType,
        value: str,  # Can be a string (command name) or a character
        position: int = -1,
        catcode: Optional[Catcode] = None,  # Use the Catcode enum for type hinting
    ):
        self.type = type
        self.value = value
        self.position = position
        self.catcode = catcode  # None for CONTROL_SEQUENCE tokens

    def __str__(self) -> str:
        if self.type == TokenType.CONTROL_SEQUENCE:
            return f"Pos {self.position:3}: {self.type.name:18} -> \\{self.value!r}"
        elif self.type == TokenType.CHARACTER:
            return f"Pos {self.position:3}: {self.type.name:18} -> {self.value!r} (Catcode {self.catcode.name if self.catcode else 'None'})"  # Print enum name
        elif self.type == TokenType.PARAMETER:
            return f"Token(PARAM='{self.value}')"
        else:
            return f"Pos {self.position:3}: {self.type.name:18} -> {self.value!r}"

    def to_str(self) -> str:
        if self.type == TokenType.CONTROL_SEQUENCE:
            return f"\\{self.value}"
        return self.value

    def copy(self) -> "Token":
        return Token(self.type, self.value, self.position, self.catcode)

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: "Token") -> bool:
        return (
            self.type == other.type
            and self.value == other.value
            # and self.position == other.position
            and self.catcode == other.catcode
        )


WHITESPACE_TOKEN = Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE)

BEGIN_ENV_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "begin")
END_ENV_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "end")

BEGIN_BRACE_TOKEN = Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP)
END_BRACE_TOKEN = Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP)

BEGIN_BRACKET_TOKEN = Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER)
END_BRACKET_TOKEN = Token(TokenType.CHARACTER, "]", catcode=Catcode.OTHER)

BACK_TICK_TOKEN = Token(TokenType.CHARACTER, "`", catcode=Catcode.OTHER)
