"""
Base class for token-based processors.

Provides core token stream operations, parsing helpers, and handler registration
that can be shared between ExpanderCore and other token processors (e.g., AMSTeX preprocessor).
"""

from logging import Logger
from typing import Callable, Dict, List, Optional

from latex2json.tokens import Catcode, Token, TokenType, Tokenizer
from latex2json.tokens.token_stream import TokenStream
from latex2json.tokens.utils import (
    is_begin_bracket_token,
    is_begin_group_token,
    is_begin_parenthesis_token,
    is_end_bracket_token,
    is_end_group_token,
    is_end_parenthesis_token,
    is_1_to_9_token,
    is_param_token,
)

# Type alias for token predicates
TokenPredicate = Callable[[Token], bool]

# Type alias for handlers: takes processor and token, returns list of tokens (or None)
Handler = Callable[["TokenProcessor", Token], Optional[List[Token]]]


class TokenProcessor:
    """
    Base class for token-based processing.

    Provides:
    - Token stream management (peek, consume, push_tokens, etc.)
    - Token parsing helpers (parse_brace_as_tokens, skip_whitespace, etc.)
    - Handler registration and dispatch
    - A process() loop for walking tokens and calling handlers
    """

    def __init__(
        self,
        tokenizer: Optional[Tokenizer] = None,
        logger: Optional[Logger] = None,
    ):
        self.logger = logger if logger is not None else Logger(__name__)
        self.tokenizer = tokenizer if tokenizer is not None else Tokenizer()
        self.stream = TokenStream(self.tokenizer)

        # Handler registry: command name -> handler function
        self._handlers: Dict[str, Handler] = {}

    # =========================================================================
    # Handler Registration
    # =========================================================================

    def register_handler(self, name: str, handler: Handler) -> None:
        """
        Register a handler for a command.

        Args:
            name: Command name with backslash (e.g., "\\proclaim")
            handler: Function that takes (processor, token) and returns List[Token] or None
        """
        self._handlers[name] = handler

    def get_handler(self, token: Token) -> Optional[Handler]:
        """Get the handler for a token, if one exists."""
        if token.type == TokenType.CONTROL_SEQUENCE:
            name = "\\" + token.value
            return self._handlers.get(name)
        elif token.catcode == Catcode.ACTIVE:
            return self._handlers.get(token.value)
        return None

    def has_handler(self, token: Token) -> bool:
        """Check if a handler exists for this token."""
        return self.get_handler(token) is not None

    # =========================================================================
    # Token Stream Operations
    # =========================================================================

    def peek(self, offset: int = 0) -> Optional[Token]:
        """Peek at the next token without consuming it."""
        return self.stream.peek(offset)

    def consume(self) -> Optional[Token]:
        """Consume and return the next token."""
        return self.stream.consume()

    def push_tokens(self, tokens: List[Token]) -> None:
        """Push tokens onto the front of the stream."""
        self.stream.push_tokens([t for t in tokens if t is not None])

    def push_text(self, text: str, source_file: Optional[str] = None) -> None:
        """Push text onto the stream for tokenization."""
        self.stream.push_text(text, source_file=source_file)

    def set_text(self, text: str) -> None:
        """Reset stream with new text."""
        self.stream.set_text(text)

    def eof(self) -> bool:
        """Check if the stream is exhausted."""
        return self.stream.eof()

    def clear(self) -> None:
        """Clear the token stream."""
        self.stream.clear()

    # =========================================================================
    # Whitespace Handling
    # =========================================================================

    def skip_whitespace(self) -> None:
        """Skip whitespace tokens (including newlines)."""
        self.stream.skip_whitespace()

    def skip_whitespace_not_eol(self) -> int:
        """Skip whitespace but not end-of-line. Returns count of spaces skipped."""
        space_cnt = 0
        while not self.eof():
            tok = self.peek()
            if tok is None:
                break
            if tok.type == TokenType.CHARACTER and tok.catcode == Catcode.SPACE:
                self.consume()
                space_cnt += 1
            else:
                break
        return space_cnt

    # =========================================================================
    # Matching and Predicates
    # =========================================================================

    def match(
        self,
        token_type: Optional[TokenType] = None,
        value: Optional[str] = None,
        catcode: Optional[Catcode] = None,
    ) -> bool:
        """Check if the next token matches the given criteria."""
        return self.stream.match(token_type, value, catcode)

    @staticmethod
    def is_control_sequence(tok: Token) -> bool:
        """Check if token is a control sequence or active character."""
        return tok.type == TokenType.CONTROL_SEQUENCE or tok.catcode == Catcode.ACTIVE

    # =========================================================================
    # Catcode Management
    # =========================================================================

    def set_catcode(self, char_ord: int, catcode: Catcode) -> None:
        """Set the catcode for a character."""
        self.tokenizer.set_catcode(char_ord, catcode)

    def get_catcode(self, char_ord: int) -> Catcode:
        """Get the catcode for a character."""
        return self.tokenizer.get_catcode(char_ord)

    # =========================================================================
    # Verbatim Mode
    # =========================================================================

    def _set_verbatim_mode(self, verbatim: bool) -> None:
        """Enable/disable verbatim mode on the stream."""
        if verbatim:
            self.stream.set_verbatim_mode(True)

    def _reset_verbatim_mode(self, verbatim: bool) -> None:
        """Reset verbatim mode if it was enabled."""
        if verbatim:
            self.stream.set_verbatim_mode(False)

    # =========================================================================
    # Token Parsing Helpers
    # =========================================================================

    def parse_token(self, verbatim: bool = False) -> Optional[Token]:
        """
        Parse and return the next token.

        Handles parameter tokens (#N) specially unless in verbatim mode.
        """
        if verbatim:
            return self.consume()

        tok = self.peek()
        if tok is None:
            self.consume()
            if not self.eof():
                return self.parse_token(verbatim=verbatim)
            return None

        if is_param_token(tok):
            param = self._parse_parameter_token()
            if param:
                return param

        return self.consume()

    def _parse_parameter_token(self) -> Optional[Token]:
        """
        Parse a TeX parameter sequence (#N) or escaped hash (##).

        Assumes current token is '#' with Catcode.PARAMETER.
        """
        tok = self.peek()
        if not tok or not is_param_token(tok):
            return None

        self.consume()  # Consume the '#'
        tok = self.peek()

        if tok is None:
            self.logger.error("Unexpected end of input after '#'")
            return None

        # ## -> literal #
        if is_param_token(tok):
            self.consume()
            return tok

        # #N -> Parameter token
        if is_1_to_9_token(tok):
            self.consume()
            return Token(TokenType.PARAMETER, tok.value)

        self.logger.info(f"Illegal token: {tok} after '#'. Skipping.")
        return None

    def parse_tokens_until(
        self,
        predicate: TokenPredicate,
        consume_predicate: bool = False,
        verbatim: bool = False,
    ) -> List[Token]:
        """
        Parse tokens until predicate returns True.

        Args:
            predicate: Function that returns True when we should stop
            consume_predicate: If True, consume the matching token
            verbatim: If True, parse in verbatim mode
        """
        out = []
        self._set_verbatim_mode(verbatim)
        try:
            while not self.eof():
                tok = self.parse_token(verbatim=verbatim)
                if tok is None:
                    break
                if predicate(tok):
                    if not consume_predicate:
                        self.push_tokens([tok])
                    break
                out.append(tok)
        finally:
            self._reset_verbatim_mode(verbatim)
        return out

    def parse_begin_end_as_tokens(
        self,
        begin_predicate: TokenPredicate,
        end_predicate: TokenPredicate,
        check_first_token: bool = True,
        verbatim: bool = False,
    ) -> Optional[List[Token]]:
        """
        Parse tokens between matching begin/end delimiters.

        Handles nested delimiters correctly. The outermost delimiters are NOT
        included in the returned list.

        Args:
            begin_predicate: Predicate for opening delimiter
            end_predicate: Predicate for closing delimiter
            check_first_token: If True, verify first token matches begin_predicate
            verbatim: If True, parse in verbatim mode
        """
        first_token = self.peek()
        if not first_token:
            return None

        if check_first_token:
            if not begin_predicate(first_token):
                return None
            self.consume()

        self._set_verbatim_mode(verbatim)
        try:
            out_tokens: List[Token] = []
            depth = 1

            while depth > 0:
                current_token = self.peek()

                if current_token is None:
                    self.logger.info(
                        "Unmatched braces: Reached end of stream within a definition."
                    )
                    break

                if begin_predicate(current_token):
                    depth += 1
                elif end_predicate(current_token):
                    depth -= 1

                current_token = self.parse_token(verbatim=verbatim)

                if depth > 0:
                    out_tokens.append(current_token)

            return out_tokens
        finally:
            self._reset_verbatim_mode(verbatim)

    def parse_brace_as_tokens(
        self, expand: bool = False, verbatim: bool = False
    ) -> Optional[List[Token]]:
        """Parse content within {...} braces."""
        tokens = self.parse_begin_end_as_tokens(
            is_begin_group_token, is_end_group_token, verbatim=verbatim
        )
        if expand and tokens:
            tokens = self.expand_tokens(tokens)
        return tokens

    def parse_bracket_as_tokens(
        self, expand: bool = False, verbatim: bool = False
    ) -> Optional[List[Token]]:
        """Parse content within [...] brackets."""
        tokens = self.parse_begin_end_as_tokens(
            is_begin_bracket_token, is_end_bracket_token, verbatim=verbatim
        )
        if expand and tokens:
            tokens = self.expand_tokens(tokens)
        return tokens

    def parse_parenthesis_as_tokens(
        self, expand: bool = False, verbatim: bool = False
    ) -> Optional[List[Token]]:
        """Parse content within (...) parentheses."""
        tokens = self.parse_begin_end_as_tokens(
            is_begin_parenthesis_token, is_end_parenthesis_token, verbatim=verbatim
        )
        if expand and tokens:
            tokens = self.expand_tokens(tokens)
        return tokens

    def parse_immediate_token(
        self, expand: bool = False, skip_whitespace: bool = False
    ) -> Optional[List[Token]]:
        """
        Parse the next token or braced group.

        If next token is '{', parses the entire braced content.
        Otherwise returns just the single token.
        """
        if skip_whitespace:
            self.skip_whitespace()

        tok = self.peek()
        if not tok:
            return None

        if is_begin_group_token(tok):
            tokens = self.parse_brace_as_tokens()
        else:
            tokens = [self.consume()]

        if expand and tokens:
            return self.expand_tokens(tokens)
        return tokens

    # =========================================================================
    # Token Conversion Utilities
    # =========================================================================

    def convert_str_to_tokens(
        self, text: str, catcode: Optional[Catcode] = None
    ) -> List[Token]:
        """Convert a string to a list of character tokens."""
        out = []
        for char in text:
            c = catcode or self.get_catcode(ord(char))
            out.append(Token(TokenType.CHARACTER, char, catcode=c))
        return out

    @staticmethod
    def convert_tokens_to_str(tokens: List[Token]) -> str:
        """Convert a list of tokens to a string."""
        return "".join(t.to_str() for t in tokens if t is not None)

    @staticmethod
    def check_tokens_equal(a: List[Token], b: List[Token]) -> bool:
        """Check if two token lists are equal."""
        if len(a) != len(b):
            return False
        return all(a_tok == b_tok for a_tok, b_tok in zip(a, b))

    # =========================================================================
    # Expansion (Override in Subclasses)
    # =========================================================================

    def expand_tokens(self, tokens: List[Token]) -> List[Token]:
        """
        Expand tokens. Override in subclasses that support expansion.

        Default implementation returns tokens unchanged.
        """
        return tokens

    # =========================================================================
    # Processing Loop
    # =========================================================================

    def process(self) -> List[Token]:
        """
        Process all tokens in the stream.

        For each token:
        - If a handler exists, call it and use the returned tokens
        - Otherwise, keep the token as-is

        Returns the fully processed token list.
        """
        output: List[Token] = []

        while not self.eof():
            tok = self.peek()
            if tok is None:
                self.consume()
                continue

            handler = self.get_handler(tok)
            if handler:
                self.consume()  # Consume the command token
                result = handler(self, tok)
                if result:
                    output.extend(result)
            else:
                output.append(self.consume())

        return output

    def process_text(self, text: str) -> List[Token]:
        """Process text and return the resulting tokens."""
        self.set_text(text)
        return self.process()
