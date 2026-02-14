from abc import ABC, abstractmethod
from typing import Optional, List

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_whitespace_token


class TokenSource(ABC):
    @abstractmethod
    def consume(self) -> Optional[Token]:
        pass

    @abstractmethod
    def peek(self, n: int = 0) -> Optional[Token]:
        pass

    @abstractmethod
    def eof(self) -> bool:
        pass

    def activate(self):
        pass

    def deactivate(self):
        pass


class StringSource(TokenSource):
    """Tokenizes string content using shared tokenizer"""

    def __init__(
        self,
        content: str,
        shared_tokenizer: Tokenizer,
        source_file: Optional[str] = None,
    ):
        self.content = content
        self.source_file = str(source_file) if source_file else None
        # Keep reference to shared tokenizer for catcode version tracking
        self._shared_tokenizer = shared_tokenizer
        # Create new tokenizer with same settings (shares catcode table by reference)
        self.tokenizer = Tokenizer()
        self.tokenizer.set_catcode_table(shared_tokenizer._catcodes)
        self.tokenizer.verbatim_mode = shared_tokenizer.verbatim_mode
        self.tokenizer.set(content)
        # Peek cache for O(1) lookahead
        self._peek_cache: Optional[Token] = None
        self._peek_pos: int = 0  # Position AFTER the cached token
        self._peek_catcode_version: int = 0  # Catcode version when token was cached

    def activate(self):
        pass

    def deactivate(self):
        pass

    def _is_cache_valid(self) -> bool:
        """Check if peek cache is valid (catcodes haven't changed)."""
        return (
            self._peek_cache is not None
            and self._peek_catcode_version == self._shared_tokenizer._catcode_version
        )

    def consume(self) -> Optional[Token]:
        # Use cached token if available and catcodes haven't changed
        if self._is_cache_valid():
            token = self._peek_cache
            self._peek_cache = None
            # Advance tokenizer to position after the cached token
            self.tokenizer.pos = self._peek_pos
        else:
            self._peek_cache = None  # Invalidate stale cache
            token = self.tokenizer.get_next_token()
        if token and self.source_file:
            token.source_file = self.source_file
        return token

    def peek(self, n: int = 0) -> Optional[Token]:
        # Fast path: return cached token for n=0 if catcodes haven't changed
        if n == 0 and self._is_cache_valid():
            return self._peek_cache

        saved_pos = self.tokenizer.pos
        token = None

        # Get the nth token ahead
        for _ in range(n + 1):
            token = self.tokenizer.get_next_token()
            if token is None:
                break

        # Cache the result for n=0 (save position BEFORE restoring)
        if n == 0:
            self._peek_cache = token
            self._peek_pos = self.tokenizer.pos  # Position after token
            self._peek_catcode_version = self._shared_tokenizer._catcode_version

        # Restore position
        self.tokenizer.pos = saved_pos

        return token

    def eof(self) -> bool:
        return self.tokenizer.pos >= len(self.content)


class TokenListSource(TokenSource):
    """Uses pre-tokenized tokens (for simple macro expansion)"""

    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.index = 0

    def consume(self) -> Optional[Token]:
        if self.index < len(self.tokens):
            token = self.tokens[self.index]
            self.index += 1
            return token
        return None

    def peek(self, n: int = 0) -> Optional[Token]:
        idx = self.index + n
        return self.tokens[idx] if idx < len(self.tokens) else None

    def eof(self) -> bool:
        return self.index >= len(self.tokens)


class TokenStream:
    def __init__(self, tokenizer: Optional[Tokenizer] = None):
        self.tokenizer = tokenizer or Tokenizer()
        self.source_stack: List[TokenSource] = []
        self._active_source: Optional[TokenSource] = None

    def clear(self):
        if self._active_source:
            self._active_source.deactivate()
            self._active_source = None
        self.source_stack = []

    def _ensure_active_source(self):
        """Ensure the top source is activated"""
        if self.source_stack:
            top_source = self.source_stack[-1]
            if self._active_source != top_source:
                if self._active_source:
                    self._active_source.deactivate()
                top_source.activate()
                self._active_source = top_source

    def _cleanup_exhausted_sources(self):
        """Remove exhausted sources from the top of the stack"""
        while self.source_stack and self.source_stack[-1].eof():
            if self._active_source == self.source_stack[-1]:
                self._active_source.deactivate()
                self._active_source = None
            self.source_stack.pop()

    def consume(self) -> Optional[Token]:
        self._cleanup_exhausted_sources()
        if not self.source_stack:
            return None

        self._ensure_active_source()
        token = self._active_source.consume()

        if token is None:
            self._cleanup_exhausted_sources()

        return token

    def set_text(self, text: str, source_file: Optional[str] = None):
        """Reset stream with new text"""
        self.clear()
        self.push_text(text, source_file=source_file)

    def push_text(self, text: str, source_file: Optional[str] = None):
        """Push string content for tokenization (files, macros, etc.)"""
        # Deactivate current StringSource if it exists
        self._push_source(StringSource(text, self.tokenizer, source_file=source_file))

    def push_tokens(self, tokens: List[Token]):
        """Push pre-tokenized tokens (for simple macro expansion)"""
        if not tokens:  # Don't create empty sources
            return
        self._push_source(TokenListSource(tokens))

    def _push_source(self, source: TokenSource):
        if self._active_source:
            self._active_source.deactivate()
            self._active_source = None
        self.source_stack.append(source)
        source.activate()
        self._active_source = source

    def pop_source(self):
        """Pop the current source and handle activation"""
        if self.source_stack:
            if self._active_source == self.source_stack[-1]:
                self._active_source.deactivate()
                self._active_source = None
            self.source_stack.pop()

    def pop_tokens(self):
        """Pop the current token list source if it exists"""
        if self.source_stack and isinstance(self.source_stack[-1], TokenListSource):
            self.pop_source()

    def peek(self, n: int = 0) -> Optional[Token]:
        self._cleanup_exhausted_sources()
        if not self.source_stack:
            return None

        self._ensure_active_source()
        return self._active_source.peek(n)

    def eof(self) -> bool:
        self._cleanup_exhausted_sources()
        return len(self.source_stack) == 0

    def set_catcode(self, char_code: int, catcode: Catcode):
        """Change catcodes globally across all sources"""
        self.tokenizer.set_catcode(char_code, catcode)
        # Note: peek cache invalidation is handled automatically via catcode version checking

    def set_verbatim_mode(self, verbatim: bool):
        """Set verbatim mode on the shared tokenizer and all active sources"""
        self.tokenizer.verbatim_mode = verbatim
        # Also update all StringSource tokenizers to keep them in sync
        for source in self.source_stack:
            if isinstance(source, StringSource):
                source.tokenizer.verbatim_mode = verbatim

    def skip_whitespace(self):
        while not self.eof():
            next_token = self.peek()
            if not next_token or not is_whitespace_token(next_token):
                break
            self.consume()

    def get_current_source(self) -> Optional[TokenSource]:
        if self.source_stack:
            return self.source_stack[-1]
        return None

    def get_current_source_file(self) -> Optional[str]:
        """Get the source file from the top StringSource in the stack."""
        # Iterate from top of stack backwards to find first StringSource with source_file
        for source in reversed(self.source_stack):
            if isinstance(source, StringSource) and source.source_file:
                return source.source_file
        return None

    def has_source(self, source: TokenSource) -> bool:
        return source in self.source_stack

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
        self.skip_whitespace()

        tok = self.peek()  # TokenStream.peek handles skipping ignored
        if tok is None:
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

        return is_match


if __name__ == "__main__":
    stream = TokenStream()
    stream.push_text("Hello, world!")
    print(stream.consume())
