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

    def __init__(self, content: str, shared_tokenizer: Tokenizer):
        self.content = content
        # Create new tokenizer with same settings
        self.tokenizer = Tokenizer()
        self.tokenizer.set_catcode_table(shared_tokenizer._catcodes)
        self.tokenizer.set(content)
        # self.current_pos = 0

    def activate(self):
        pass

    def deactivate(self):
        pass
        # self.current_pos = self.tokenizer.pos

    def consume(self) -> Optional[Token]:
        return self.tokenizer.get_next_token()

    def peek(self, n: int = 0) -> Optional[Token]:
        saved_pos = self.tokenizer.pos
        token = None

        # Get the nth token ahead
        for _ in range(n + 1):
            token = self.tokenizer.get_next_token()
            if token is None:
                break

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

    def set_text(self, text: str):
        """Reset stream with new text"""
        self.clear()
        self.push_text(text)

    def push_text(self, text: str):
        """Push string content for tokenization (files, macros, etc.)"""
        # Deactivate current StringSource if it exists
        self._push_source(StringSource(text, self.tokenizer))

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

    def skip_whitespace(self):
        while not self.eof():
            next_token = self.peek()
            if not next_token or not is_whitespace_token(next_token):
                break
            self.consume()

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
