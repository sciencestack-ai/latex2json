from collections import deque
from typing import Deque, List, Optional, Tuple, Union

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_whitespace_token

TokensBuffer = List[Tuple[List[Token], int]]  # List of (tokens, position at tokens)


class BaseTokenStream:
    """Base class for all token streams, providing common buffer management."""

    def __init__(self):
        self._buffer: TokensBuffer = []  # List of (tokens, position at tokens)

    def has_buffer(self):
        return len(self._buffer) > 0

    def get_buffer_stacks(self):
        return len(self._buffer)

    def get_pos(self) -> Tuple[int, int]:
        """Get current position as (position, stack_depth)."""
        if self._buffer:
            return (self._buffer[-1][1], len(self._buffer))
        return self._get_base_pos()

    def _get_base_pos(self) -> Tuple[int, int]:
        """Get position from the underlying source when no buffers are active."""
        return (0, 0)  # Default implementation

    def set_pos(self, pos: int, stack_index: int = 0):
        """Set position at specified stack level."""
        if stack_index == 0:
            self._set_base_pos(pos)
            return
        stack_index -= 1
        if 0 <= stack_index < len(self._buffer):
            self._buffer[stack_index] = (self._buffer[stack_index][0], pos)

    def _set_base_pos(self, pos: int):
        """Set position in the underlying source."""
        pass  # Default implementation

    def push_tokens(self, tokens: List[Token]):
        self._buffer.append((tokens, 0))

    def pop_tokens(self):
        if len(self._buffer) > 0:
            self._buffer.pop()
            return True
        return False

    def reset(self):
        self.set_pos(0, stack_index=len(self._buffer))

    def clear(self):
        self._buffer = []

    def consume(self) -> Optional[Token]:
        while self._buffer:
            tokens, idx = self._buffer[-1]
            if idx < len(tokens):
                token = tokens[idx]
                self._buffer[-1] = (tokens, idx + 1)
                return token
            else:
                self._buffer.pop()
        return self._consume_base()

    def _consume_base(self) -> Optional[Token]:
        """Consume from the underlying source."""
        return None  # Default implementation

    def peek(self, n: int = 0) -> Optional[Token]:
        while self._buffer:
            tokens, idx = self._buffer[-1]
            if tokens is None:
                self._buffer.pop()
                continue
            if idx + n < len(tokens):
                return tokens[idx + n]
            else:
                self._buffer.pop()
        return self._peek_base(n)

    def _peek_base(self, n: int) -> Optional[Token]:
        """Peek from the underlying source."""
        return None  # Default implementation

    def eof(self) -> bool:
        return self.peek() is None

    def skip_whitespace(self):
        """Skip all consecutive whitespace tokens."""
        start_pos, start_stack = self.get_pos()
        prev_pos_table: List[Tuple[int, int]] = [self._get_base_pos()]
        for i, (tokens, idx) in enumerate(self._buffer):
            prev_pos_table.append((idx, i + 1))

        while not self.eof():
            next_token = self.peek()
            if not next_token or not is_whitespace_token(next_token):
                break
            self.consume()

        cur_pos, cur_stack = self.get_pos()
        if cur_stack != start_stack:
            return prev_pos_table[cur_stack]
        return (start_pos, start_stack)

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
            self.set_pos(*start_pos)
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

        self.set_pos(*start_pos)
        return False


class TokenStream(BaseTokenStream):
    """Stream that reads tokens from a Tokenizer."""

    def __init__(self, tokenizer: Tokenizer):
        super().__init__()
        self.tokenizer = tokenizer

    def clear(self):
        super().clear()
        self.tokenizer.set("")

    def _get_base_pos(self) -> Tuple[int, int]:
        return (self.tokenizer.pos, 0)

    def _set_base_pos(self, pos: int):
        self.tokenizer.pos = pos

    def set_text(self, text: str):
        self.clear()
        self.tokenizer.set(text)

    def _consume_base(self) -> Optional[Token]:
        return self.tokenizer.get_next_token()

    def _peek_base(self, n: int) -> Optional[Token]:
        if n < 0:
            raise NotImplementedError("negative n not supported")
        start_pos = self.tokenizer.pos
        i = 0
        out = None
        while i <= n and not self.tokenizer.eof():
            out = self.tokenizer.get_next_token()
            if out is None:
                break
            i += 1
        self.tokenizer.pos = start_pos
        return out


TokenSource = Union[List[Token], BaseTokenStream]


class MultiTokenStream:  # This is the main, stack-based stream manager
    def __init__(self, initial_source: List[TokenSource]):
        # The stack stores (current_source_object, current_index_for_list_source)
        # For TokenStream, the index is internally managed by the source itself.
        self._stack: List[Tuple[TokenSource, int]] = []
        for source in initial_source:
            if isinstance(source, List):
                self._stack.append((source, 0))
            else:  # Assumed TokenStream
                self._stack.append((source, 0))

    def push_tokens(self, tokens: TokenSource):
        """Pushes a list of tokens onto the stream stack (e.g., for macro expansion)."""
        self._stack.append((tokens, 0))  # Start at index 0 for this new list

    def pop_tokens(self):
        """Pops the last list of tokens from the stack."""
        """Pops the current source from the stack if it's exhausted."""
        if len(self._stack) > 1:  # Always keep at least the base stream
            self._stack.pop()
            return True
        return False  # Cannot pop the base stream

    def peek(self) -> Optional[Token]:
        """Peeks the next token from the active source on the stack."""
        while self._stack:
            current_source, current_idx = self._stack[-1]

            if isinstance(current_source, List):
                if current_idx < len(current_source):
                    return current_source[current_idx]
                else:  # This List is exhausted
                    if not self.pop_tokens():
                        return None  # All sources exhausted
            else:  # Must be a TokenStream
                token = current_source.peek()
                if token is not None:
                    return token
                else:  # This TokenStream is exhausted
                    if not self.pop_tokens():
                        return None  # All sources exhausted
        return None  # Stack is empty

    def consume(self) -> Optional[Token]:
        """Consumes and returns the next token from the active source on the stack."""
        # Similar logic to peek_token, but advances the index/source
        while self._stack:
            current_source, current_idx = self._stack[-1]

            if isinstance(current_source, List):
                if current_idx < len(current_source):
                    token = current_source[current_idx]
                    self._stack[-1] = (
                        current_source,
                        current_idx + 1,
                    )  # Advance index for list
                    return token
                else:  # List is exhausted
                    if not self.pop_tokens():
                        return None
            else:  # Must be a TokenStream
                token = (
                    current_source.consume()
                )  # This advances the source's internal state
                if token is not None:
                    return token
                else:  # TokenStream is exhausted
                    if not self.pop_tokens():
                        return None
        return None  # Stack is empty

    def eof(self) -> bool:
        """Checks if the entire stream stack is exhausted."""
        return self.peek() is None

    def skip_whitespace(self) -> int:
        """Consumes all consecutive CHARACTER tokens with Catcode.SPACE."""
        start_pos_or_indicator = -1  # A way to indicate if any whitespace was skipped
        while not self.eof():
            next_token = self.peek()
            if not next_token or not is_whitespace_token(next_token):
                break
            # Only consume if it's whitespace
            self.consume()
            if start_pos_or_indicator == -1:  # Indicate that whitespace was found
                start_pos_or_indicator = 0  # Or a real pos if you can map back to file

        return start_pos_or_indicator  # This return value might need rethinking for mixed sources


if __name__ == "__main__":
    tokenizer = Tokenizer()
    stream = TokenStream(tokenizer)
    tokenizer.set("Hello, world!")
    print(stream.consume())
