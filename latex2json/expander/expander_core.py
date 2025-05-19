from logging import Logger
from typing import Callable, List, Any, Dict, Optional, Type

from latex2json.expander.macro_registry import (
    Handler,
    Macro,
    MacroRegistry,
)

from latex2json.expander.state import ExpanderState
from latex2json.tokens import Catcode, Token, TokenType, Tokenizer
from latex2json.tokens.token_stream import (
    TokenStream,
)
from latex2json.tokens.types import BEGIN_BRACE_TOKEN, END_BRACE_TOKEN
from latex2json.tokens.utils import (
    is_1_to_9_token,
    is_text_token,
    is_integer_token,
    is_digit_token,
    is_param_token,
)

# arbitrary character that is not a valid token
STOP_TOKEN = Token(TokenType.CHARACTER, r"\0", catcode=Catcode.OTHER)


class ExpanderCore:
    """
    The main engine for processing the document.
    Drives parsing, manages state, executes commands, and performs expansion.
    """

    def __init__(
        self,
        tokenizer: Tokenizer = Tokenizer(),
        logger: Logger = Logger("expander"),
    ):
        self.tokenizer = tokenizer
        self.stream = TokenStream(tokenizer)
        self.state = ExpanderState(tokenizer)  # The stack of state layers
        self.logger = logger

    @property
    def macros(self) -> MacroRegistry:
        return self.state.current.macro_registry

    def register_macro(self, name: str, macro: Macro, is_global: bool = False):
        self.macros.set(name, macro, is_global=is_global)

    def register_handler(self, name: str, handler: Handler, is_global: bool = False):
        self.macros.register_handler(name, handler, is_global=is_global)

    def set_text(self, text: str):
        self.stream.set_text(text)

    def eof(self) -> bool:
        return self.stream.eof()

    def expand(self, text: str) -> List[Token]:
        self.set_text(text)
        return self.process()

    def expand_tokens(self, tokens: List[Token]) -> List[Token]:
        self.stream.push_tokens(tokens + [STOP_TOKEN])
        return self.process(stop_token=STOP_TOKEN)

    def process(self, stop_token: Optional[Token] = None) -> List[Token]:
        """
        Processes the entire token stream, performing expansions and executing side effects,
        until the stop token is encountered.
        """
        final_expanded_tokens: List[Token] = []

        while not self.eof():
            current_token = self.peek()  # Peek at the next token

            if current_token is None:  # Should be caught by eof(), but defensive check
                break
            if stop_token and current_token == stop_token:
                self.consume()
                break

            final_expanded_tokens.extend(self.parse())

        return final_expanded_tokens

    def push_scope(self):
        self.state.push_scope()

    def pop_scope(self):
        self.state.pop_scope()

    def peek(self) -> Optional[Token]:
        return self.stream.peek()

    def consume(self) -> Optional[Token]:
        return self.stream.consume()

    def skip_whitespace(self):
        return self.stream.skip_whitespace()

    def parse(self) -> Optional[List[Token]]:
        tok = self.peek()
        if tok is None:
            return None
        if is_param_token(tok):
            param = self.parse_parameter_token()
            if param:
                return [param]

        if tok.type == TokenType.CONTROL_SEQUENCE:
            macro = self.macros.get(tok.value)
            if macro:
                self.consume()  # Consume the control sequence token itself
                processed = macro.handler(self, tok)
                return processed
        return [self.consume()]

    # parser helper functions
    def match_token(self, tok: Token) -> bool:
        """Checks if the next non-ignored token matches the given token."""
        return self.match(
            token_type=tok.type,
            value=tok.value,
            catcode=tok.catcode,
        )

    # The match method now checks against the new Token structure (type and catcode)
    def match(
        self,
        token_type: Optional[TokenType] = None,
        value: Optional[str] = None,
        catcode: Optional[Catcode] = None,
    ) -> bool:
        """
        Checks if the next non-ignored token matches the criteria.
        Can match by TokenType, Catcode, or Value.
        """
        # skip whitespace?
        start_pos = self.skip_whitespace()

        tok = self.peek()  # TokenStream.peek handles skipping ignored
        if tok is None:
            self.stream.set_pos(*start_pos)
            return False

        type_match = token_type is None or tok.type == token_type
        catcode_match = catcode is None or tok.catcode == catcode
        value_match = value is None or tok.value == value

        # For CHARACTER tokens, catcode is the primary discriminator after type
        is_match = False
        if tok.type == TokenType.CHARACTER:
            is_match = type_match and catcode_match and value_match
            # Value match is less common for characters
        # For CONTROL_SEQUENCE tokens, value is the primary discriminator after type
        elif tok.type == TokenType.CONTROL_SEQUENCE:
            is_match = type_match and value_match
            # Catcode is implicitly 0 for the backslash, not on the token itself
        # Default for other token types (if any)
        else:
            is_match = (
                type_match and value_match
            )  # Or adjust based on other token types

        if is_match:
            return True

        self.stream.set_pos(*start_pos)
        return False

    def _combine_sequence_as_str(self, predicate: Callable[[Token], bool]):
        tok = self.peek()
        out = ""
        while tok and predicate(tok):
            out += tok.value
            self.consume()
            tok = self.peek()
        return out

    def parse_immediate_token(self) -> List[Token] | None:
        tok = self.peek()
        if not tok:
            return None

        if tok == BEGIN_BRACE_TOKEN:
            return self.parse_brace_as_tokens()
        return self.parse()

    def parse_integer(self) -> int:
        sequence = self._combine_sequence_as_str(is_integer_token)
        if not sequence:
            return None
        return int(sequence)

    def parse_float(self) -> float:
        sequence = self._combine_sequence_as_str(is_digit_token)
        if not sequence:
            return None
        return float(sequence)

    def parse_equals(self) -> bool:
        if self.match(value="=", catcode=Catcode.OTHER):
            self.consume()
            return True
        return False

    def parse_angle_brackets(self) -> str:
        if self.match(value="<", catcode=Catcode.OTHER) or self.match(
            value=">", catcode=Catcode.OTHER
        ):
            return self.consume().value
        return None

    # simulate Tex engine behavior of parsing #1 -> Parameter token '1', ##1 -> "#", 1
    def parse_parameter_token(self) -> Optional[Token]:
        """
        Parses a TeX parameter sequence (#N) or an escaped hash (##) from the stream,
        as encountered when parsing a macro definition body.

        This function assumes the current token being peeked at is a
        '#' character with Catcode.PARAMETER.

        Returns:
            A single Token representing the parsed parameter (#N) or literal hash (#),
            or None if there's a syntax error (e.g., # followed by non-digit/non-#).
        """
        # Ensure we are starting with a '#' token with Catcode.PARAMETER
        # This check is defensive, as the caller should ensure this.
        tok = self.peek()
        if not tok:
            return None
        if not is_param_token(tok):
            print(
                f"WARNING: parse_parameter_sequence called without current Catcode.PARAMETER: {tok}"
            )
            return None  # Not the start of a parameter sequence

        # Consume the initial '#' token
        self.consume()

        # Peek the token immediately following the first '#'
        tok = self.peek()

        if tok is None:
            print(
                "Error: Unexpected end of input after '#'. Expected a digit (1-9) or another '#'."
            )
            return None  # Syntax error: incomplete sequence

        # Case 1: ## -> Literal '#'
        if is_param_token(tok):
            self.consume()  # Consume the second '#'
            return tok  # return as literal #

        # Case 2: #N -> Parameter token (N must be 1-9)
        if is_1_to_9_token(tok):  # Check for digits '1' through '9'
            self.consume()  # Consume the digit
            return Token(TokenType.PARAMETER, tok.value)

        # Case 3: # followed by something else (error in definition)
        print(
            f"Error: Illegal parameter number or escape sequence after '#'. "
            f"Found '{tok.value}' (type: {tok.type}, catcode: {tok.catcode.name})."
        )
        return None  # Indicate an error for the parser to handle

    def parse_brace_as_tokens(self) -> List[Token]:
        """
        Parses a sequence of tokens enclosed in braces '{...}' and returns them as a List[Token].
        The outermost braces are NOT included in the returned list.
        Handles nested braces correctly.
        """
        # 1. Peek at the very first token to check for the opening brace
        first_token = self.peek()

        if not first_token or first_token != BEGIN_BRACE_TOKEN:
            return []

        # 2. Consume the opening brace itself
        self.consume()

        definition_tokens: List[Token] = []
        brace_depth = 1  # We've consumed one opening brace, so depth starts at 1

        # 3. Loop until the matching closing brace is found (brace_depth returns to 0)
        while brace_depth > 0:
            current_token = self.peek()

            if current_token is None:
                # Error: Reached the end of the input stream before finding a matching closing brace.
                print("Unmatched braces: Reached end of stream within a definition.")
                # Depending on your error handling strategy, you might raise an exception here
                # or return the partially collected tokens.
                break  # Exit loop due to error

            # Check token type and update brace_depth
            if current_token == BEGIN_BRACE_TOKEN:
                brace_depth += 1
            elif current_token == END_BRACE_TOKEN:
                brace_depth -= 1

            parsed_tokens = self.parse()

            if brace_depth > 0:
                definition_tokens.extend(parsed_tokens)

        return definition_tokens

    def set_catcode(self, char_ord: int, catcode: Catcode):
        self.state.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.state.get_catcode(char_ord)


if __name__ == "__main__":

    expander = ExpanderCore()

    text = r"""
    {
        Outer
        {
            Inner
        }
        Post
    }
    """.strip()
    expander.set_text(text)
