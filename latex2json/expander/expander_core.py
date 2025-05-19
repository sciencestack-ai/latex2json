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
from latex2json.tokens.types import BACK_TICK_TOKEN
from latex2json.tokens.utils import (
    is_1_to_9_token,
    is_begin_bracket_token,
    is_begin_group_token,
    is_end_bracket_token,
    is_end_group_token,
    is_integer_token,
    is_digit_token,
    is_param_token,
)

# arbitrary character that is not a valid token
STOP_TOKEN = Token(TokenType.CHARACTER, r"\0", catcode=Catcode.OTHER)

TokenPredicate = Callable[[Token], bool]


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

        self._init_state_macros()

    @property
    def macros(self) -> MacroRegistry:
        return self.state.current.macro_registry

    def _init_state_macros(self):
        def global_handler(expander: "ExpanderCore", token: Token):
            expander.state.pending_global = True
            return []

        self.register_handler("\\global", global_handler, is_global=True)

    def get_macro(self, name: str) -> Optional[Macro]:
        return self.state.get_macro(name)

    def register_macro(self, name: str, macro: Macro, is_global: bool = False):
        self.state.set_macro(name, macro, is_global=is_global)

    def register_handler(self, name: str, handler: Handler, is_global: bool = False):
        macro = Macro(name, handler)
        self.state.set_macro(name, macro, is_global=is_global)

    def set_text(self, text: str):
        self.stream.set_text(text)

    def eof(self) -> bool:
        return self.stream.eof()

    def expand(self, text: str) -> List[Token]:
        self.set_text(text)
        return self.process()

    def expand_tokens(self, tokens: List[Token]) -> List[Token]:
        self.stream.push_tokens(tokens + [STOP_TOKEN])
        out = self.process(stop_token_logic=lambda tok: tok is STOP_TOKEN)
        if self.peek() is STOP_TOKEN:
            self.consume()  # consume the STOP_TOKEN
        return out

    def process(self, stop_token_logic: Optional[TokenPredicate] = None) -> List[Token]:
        """
        Processes the entire token stream, performing expansions and executing side effects,
        until the stop token is encountered.
        """
        final_expanded_tokens: List[Token] = []

        while not self.eof():
            current_token = self.peek()  # Peek at the next token

            if current_token is None:  # Should be caught by eof(), but defensive check
                break
            if stop_token_logic and stop_token_logic(current_token):
                break

            processed = self._expand_next()
            if processed:
                final_expanded_tokens.extend(processed)

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

    # main parsing logic
    def _expand_next(self) -> Optional[List[Token]]:
        tok = self.parse_token()
        if tok is None:
            return None

        if tok.type == TokenType.CONTROL_SEQUENCE:
            macro = self.state.get_macro(tok.value)
            if macro:
                processed = macro.handler(self, tok)
                return processed
        else:
            self.state.pending_global = False
            if is_begin_group_token(tok):
                self.push_scope()
            elif is_end_group_token(tok):
                self.pop_scope()
        return [tok]

    def parse_token(self) -> Optional[Token]:
        tok = self.peek()
        if tok is None:
            return None
        if is_param_token(tok):
            param = self.parse_parameter_token()
            if param:
                return param
        return self.consume()

    # parser helper functions
    def match(
        self,
        token_type: Optional[TokenType] = None,
        value: Optional[str] = None,
        catcode: Optional[Catcode] = None,
    ) -> bool:
        return self.stream.match(token_type, value, catcode)

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

        if is_begin_group_token(tok):
            return self.parse_brace_as_tokens()
        return [self.consume()]

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

    def parse_asterisk(self) -> bool:
        if self.match(value="*", catcode=Catcode.OTHER):
            self.consume()
            return True
        return False

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
            self.logger.warning(
                f"WARNING: parse_parameter_sequence called without current Catcode.PARAMETER: {tok}"
            )
            return None  # Not the start of a parameter sequence

        # Consume the initial '#' token
        self.consume()

        # Peek the token immediately following the first '#'
        tok = self.peek()

        if tok is None:
            self.logger.error(
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
        self.logger.error(
            f"Error: Illegal parameter number or escape sequence after '#'. "
            f"Found '{tok.value}' (type: {tok.type}, catcode: {tok.catcode.name})."
        )
        return None  # Indicate an error for the parser to handle

    def parse_begin_end_as_tokens(
        self, begin_predicate: TokenPredicate, end_predicate: TokenPredicate
    ) -> List[Token]:
        """
        Parses a sequence of tokens enclosed in braces '{...}' and returns them as a List[Token].
        The outermost braces are NOT included in the returned list.
        Handles nested braces correctly.
        """
        # 1. Peek at the very first token to check for the opening brace
        first_token = self.peek()

        if not first_token or not begin_predicate(first_token):
            return None

        # 2. Consume the opening brace itself
        self.consume()

        out_tokens: List[Token] = []
        brace_depth = 1  # We've consumed one opening brace, so depth starts at 1

        # 3. Loop until the matching closing brace is found (brace_depth returns to 0)
        while brace_depth > 0:
            current_token = self.peek()

            if current_token is None:
                # Error: Reached the end of the input stream before finding a matching closing brace.
                self.logger.warning(
                    "Unmatched braces: Reached end of stream within a definition."
                )
                # Depending on your error handling strategy, you might raise an exception here
                # or return the partially collected tokens.
                break  # Exit loop due to error

            # Check token type and update brace_depth
            if begin_predicate(current_token):
                brace_depth += 1
            elif end_predicate(current_token):
                brace_depth -= 1

            current_token = self.parse_token()

            if brace_depth > 0:
                out_tokens.append(current_token)

        return out_tokens

    def parse_brace_as_tokens(self) -> List[Token]:
        return self.parse_begin_end_as_tokens(is_begin_group_token, is_end_group_token)

    def parse_bracket_as_tokens(self) -> List[Token]:
        return self.parse_begin_end_as_tokens(
            is_begin_bracket_token, is_end_bracket_token
        )

    def set_catcode(self, char_ord: int, catcode: Catcode):
        self.state.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        return self.state.get_catcode(char_ord)

    # converts a list of tokens into their associated macro definitions if exists
    def convert_to_macro_definitions(self, definition: List[Token]) -> List[Token]:
        final_definition = []
        for tok in definition:
            if tok.type == TokenType.CONTROL_SEQUENCE:
                macro = self.state.get_macro(tok.value)
                if macro:
                    final_definition.extend(macro.definition)
                    continue
            final_definition.append(tok)
        return final_definition

    def parse_environment_name(self) -> Optional[str]:
        self.skip_whitespace()

        tok = self.peek()
        if not tok or not is_begin_group_token(tok):
            return None

        name = self.parse_brace_as_tokens()
        name = "".join(t.value for t in name)

        return name

    def parse_char_for_catcode(self) -> Optional[str]:
        if self.peek() == BACK_TICK_TOKEN:
            self.consume()
        else:
            return None

        # check for controlsequence
        tok = self.peek()
        cmd_name: str | None = None
        if tok.type == TokenType.CONTROL_SEQUENCE:
            cmd_name = tok.value
            self.consume()
        else:
            self.logger.warning(
                f"WARNING: \\catcode expected control sequence, but found {tok.value}"
            )
            return None

        char = cmd_name
        if len(char) > 1:
            char = char[0]
            self.logger.warning(
                f"WARNING: \\catcode only takes one character, using {char}"
            )

        return char

    def convert_str_to_tokens(self, text: str) -> List[Token]:
        out = []
        for c in text:
            catcode = self.get_catcode(ord(c))
            out.append(Token(TokenType.CHARACTER, c, catcode=catcode))
        return out

    @staticmethod
    def check_tokens_equal(a: List[Token], b: List[Token]) -> bool:
        if len(a) != len(b):
            return False
        for a_tok, b_tok in zip(a, b):
            if a_tok != b_tok:
                return False
        return True


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
