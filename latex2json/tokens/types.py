from copy import deepcopy
from enum import Enum, auto
from typing import Any, List, Optional

from latex2json.tokens.catcodes import Catcode


# --- Define Token Types (based on Catcodes) ---
# These represent the fundamental types of tokens TeX produces based on catcodes.
# This enum is distinct from the Catcode enum, representing the *type* of token formed.
class TokenType(Enum):
    CONTROL_SEQUENCE = 1  # \command (name or symbol)
    CHARACTER = (
        2  # A character with a specific catcode (e.g., 'a' catcode 11, '{' catcode 1)
    )
    MATH_SHIFT_INLINE = 3  # Simulate Catcode.Mathshift=3
    MATH_SHIFT_DISPLAY = 4
    END_OF_LINE = 5  # Simulate Catcode.END_OF_LINE=5

    # PARSED types during expander i.e. not seen in tokenizer, only after expansion
    PARAMETER = 6  # Simulate Catcode.PARAMETER=6
    ENVIRONMENT_START = 7
    ENVIRONMENT_END = 8
    COMMAND_WITH_ARGS = 9  # for \section, \caption, etc

    # TODO?
    INVALID = 15  # For invalid tokens or errors


class EnvironmentType(Enum):
    DEFAULT = "default"
    EQUATION = "equation"
    EQUATION_ALIGN = "align"
    EQUATION_MATRIX_OR_ARRAY = "matrix_or_array"
    THEOREM = "theorem"
    VERBATIM = "verbatim"
    LIST = "list"


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
        source_file: Optional[str] = None,
    ):
        self.type = type
        self.value = value
        self.position = position
        self.catcode = catcode  # None for CONTROL_SEQUENCE tokens
        self.source_file = source_file

    def __str__(self) -> str:
        value = self.value

        if self.type == TokenType.CONTROL_SEQUENCE:
            return f"Pos {self.position:3}: {self.type.name:18} -> \\{value!r}"
        elif self.type == TokenType.CHARACTER:
            return f"{value!r}"
        elif self.type == TokenType.PARAMETER:
            return f"Token(PARAM='{value}')"
        else:
            return f"Pos {self.position:3}: {self.type.name:18} -> {value!r}"

    def to_str(self) -> str:
        if self.type == TokenType.CONTROL_SEQUENCE:
            return f"\\{self.value}"
        elif self.type == TokenType.ENVIRONMENT_END:
            return f"\\end{{{self.value}}}"
        return self.value

    def copy(self) -> "Token":
        return Token(
            self.type, self.value, self.position, self.catcode, self.source_file
        )

    def __repr__(self) -> str:
        return self.__str__()

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, Token):
            return False
        if type(self) != type(other):
            return False
        return (
            self.type == other.type
            and self.value == other.value
            # and self.position == other.position
            and self.catcode == other.catcode
        )


class EnvironmentStartToken(Token):
    def __init__(
        self,
        name: str,
        numbering: Optional[str] = None,
        env_type: EnvironmentType = EnvironmentType.DEFAULT,
        display_name: Optional[str] = None,
        args: Optional[List[List[Token]]] = None,
        direct_command: Optional[str] = None,
    ):
        super().__init__(TokenType.ENVIRONMENT_START, value=name)
        self.name = name
        self.numbering = numbering
        self.env_type = env_type
        self.display_name = display_name if display_name else name
        self.args = args

        if direct_command and not direct_command.startswith("\\"):
            direct_command = "\\" + direct_command
        self.direct_command = direct_command

    def copy(self) -> "EnvironmentStartToken":
        return EnvironmentStartToken(
            name=self.name,
            numbering=self.numbering,
            env_type=self.env_type,
            display_name=self.display_name,
            args=self.args.copy() if self.args else None,
        )

    def to_str(self):
        if self.direct_command:
            return self.direct_command
        return f"\\begin{{{self.name}}}"

    def __str__(self) -> str:
        out = f"{self.type.name:18} -> {self.name} ({self.display_name})"
        if self.numbering:
            out += f" [Numbering: {self.numbering}]"
        if self.env_type != EnvironmentType.DEFAULT:
            out += f" [{self.env_type.name}]"
        if self.args:
            out += f" [Args: {self.args}]"
        return out

    def __eq__(self, other: Token) -> bool:
        if not isinstance(other, EnvironmentStartToken):
            return False
        return (
            self.name == other.name
            and self.numbering == other.numbering
            and self.env_type == other.env_type
            and self.display_name == other.display_name
            # and self.args == other.args
        )


class EnvironmentEndToken(Token):
    def __init__(self, value: str, direct_command: Optional[str] = None):
        super().__init__(TokenType.ENVIRONMENT_END, value=value)
        if direct_command and not direct_command.startswith("\\"):
            direct_command = "\\" + direct_command
        self.direct_command = direct_command

    def to_str(self):
        if self.direct_command:
            return self.direct_command
        return f"\\end{{{self.value}}}"

    def __eq__(self, other: Token) -> bool:
        if other.type != TokenType.ENVIRONMENT_END:
            return False
        if other.value != self.value:
            return False
        return True


class CommandWithArgsToken(Token):
    def __init__(
        self,
        name: str,
        args: List[List[Token]] = [],
        opt_args: List[List[Token]] = [],
        numbering: Optional[str] = None,
        counter_name: Optional[str] = None,
    ):
        super().__init__(TokenType.COMMAND_WITH_ARGS, value=name)
        self.numbering = numbering
        self.name = name
        self.args = args
        self.opt_args = opt_args
        self.counter_name = counter_name

    @property
    def num_req_args(self) -> int:
        return len(self.args)

    @property
    def num_opt_args(self) -> int:
        return len(self.opt_args)

    def to_str(self):
        out = f"\\{self.name}"
        if self.opt_args:
            for arg in self.opt_args:
                out += "[" + "".join([a.to_str() for a in arg]) + "]"
        if self.args:
            for arg in self.args:
                out += "{" + "".join([a.to_str() for a in arg]) + "}"
        return out

    def to_tokens(self) -> List[Token]:
        out = [Token(TokenType.CONTROL_SEQUENCE, self.name)]
        for arg in self.opt_args:
            out.append(BEGIN_BRACKET_TOKEN.copy())
            out.extend(arg)
            out.append(END_BRACKET_TOKEN.copy())
        for arg in self.args:
            out.append(BEGIN_BRACE_TOKEN.copy())
            out.extend(arg)
            out.append(END_BRACE_TOKEN.copy())
        return out

    def copy(self) -> "CommandWithArgsToken":
        return CommandWithArgsToken(
            name=self.name,
            args=deepcopy(self.args),
            opt_args=deepcopy(self.opt_args),
            numbering=self.numbering,
            counter_name=self.counter_name,
        )

    def __eq__(self, other: Token) -> bool:
        if not isinstance(other, CommandWithArgsToken):
            return False
        return (
            super().__eq__(other)
            and self.args == other.args
            and self.opt_args == other.opt_args
            and self.numbering == other.numbering
            # and self.counter_name == other.counter_name
        )

    def __str__(self) -> str:
        out = f"{self.type.name:18} -> {self.name}"
        if self.counter_name:
            out += f" [counter:{self.counter_name}]"
        if self.numbering:
            out += f"({self.numbering})"
        if self.opt_args:
            out += (
                "[" + "".join([arg.value for arg in self.opt_args for arg in arg]) + "]"
            )
        if self.args:
            out += "{" + "".join([arg.value for arg in self.args for arg in arg]) + "}"
        return out


WHITESPACE_TOKEN = Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE)

BEGIN_ENV_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "begin")
END_ENV_TOKEN = Token(TokenType.CONTROL_SEQUENCE, "end")

BEGIN_BRACE_TOKEN = Token(TokenType.CHARACTER, "{", catcode=Catcode.BEGIN_GROUP)
END_BRACE_TOKEN = Token(TokenType.CHARACTER, "}", catcode=Catcode.END_GROUP)

BEGIN_BRACKET_TOKEN = Token(TokenType.CHARACTER, "[", catcode=Catcode.OTHER)
END_BRACKET_TOKEN = Token(TokenType.CHARACTER, "]", catcode=Catcode.OTHER)

BACK_TICK_TOKEN = Token(TokenType.CHARACTER, "`", catcode=Catcode.OTHER)
APOSTROPHE_TOKEN = Token(TokenType.CHARACTER, "'", catcode=Catcode.OTHER)
