from collections import deque
from typing import Deque, List, Optional, Tuple, Union

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_whitespace_token


# Dynamic token stream
class BaseTokenStream:
    """A stream of Tokens, fetching dynamically from a Tokenizer and skipping ignored tokens."""

    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer

    def get_pos(self):
        return (self.tokenizer.pos, 0)

    def set_pos(self, pos: int, stack_index: int = 0):
        self.tokenizer.pos = pos

    def set_text(self, text: str):
        self.tokenizer.set(text)

    def reset(self):
        self.set_pos(0)

    def peek(self, n: int = 0) -> Optional[Token]:
        """Peek at the token at the given offset from the current position."""
        start_pos = self.get_pos()[0]
        i = 0
        out = None
        while i <= n and not self.tokenizer.eof():
            out = self.tokenizer.get_next_token()
            if out is None:
                break
            i += 1
        self.set_pos(start_pos)
        return out

    def consume(self) -> Optional[Token]:
        return self.tokenizer.get_next_token()

    def eof(self) -> bool:
        """Check if the stream has reached the end."""
        return self.peek() is None

    def skip_whitespace(self):
        """Consume all consecutive CHARACTER tokens with Catcode.SPACE.
        Returns the start position pre skip
        """
        start_pos = self.get_pos()
        while not self.eof():
            next_token = self.peek()
            if not next_token or is_whitespace_token(next_token):
                self.consume()
            else:
                break
        return start_pos


TokensBuffer = List[Tuple[List[Token], int]]  # List of (tokens, position at tokens)


class TokenStream(BaseTokenStream):
    def __init__(self, tokenizer: Tokenizer):
        super().__init__(tokenizer)
        self._buffer: TokensBuffer = []

    def has_buffer(self):
        return len(self._buffer) > 0

    def get_buffer_stacks(self):
        return len(self._buffer)

    def get_pos(self) -> Tuple[int, int]:
        """Get current position as (position, stack_depth).

        Returns:
            Tuple[int, int]: (current_position, stack_depth) where:
                - current_position is the index in current buffer or base stream
                - stack_depth is number of active buffers (0 for base stream)
        """
        if self._buffer:
            return (self._buffer[-1][1], len(self._buffer))
        return super().get_pos()

    def set_pos(self, pos: int, stack_index: int = 0):
        """Set position at specified stack level.

        Args:
            pos: Position to set
            stack_index: Stack level (0 for base stream, 1+ for buffer layers)
        """
        if stack_index == 0:
            super().set_pos(pos, 0)
            return
        stack_index -= 1
        if 0 <= stack_index < len(self._buffer):
            self._buffer[stack_index] = (self._buffer[stack_index][0], pos)

    def push_tokens(self, tokens: List[Token]):
        self._buffer.append((tokens, 0))

    def pop_tokens(self):
        if len(self._buffer) > 0:
            self._buffer.pop()
            return True
        return False

    def set_text(self, text: str):
        super().set_text(text)
        self._buffer = []

    def reset(self):
        super().reset()
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
        return super().consume()

    def peek(self, n: int = 0) -> Optional[Token]:
        while self._buffer:
            tokens, idx = self._buffer[-1]
            if idx + n < len(tokens):
                return tokens[idx + n]
            else:
                self._buffer.pop()
        return super().peek(n)

    def skip_whitespace(self):
        """Skip all consecutive whitespace tokens, handling transitions between buffer layers.

        This method needs special handling because whitespace skipping might consume
        tokens across multiple buffer layers. For example, we might:
        - Start in buffer layer 2
        - Skip whitespace in buffer 2
        - Continue through buffer 1
        - End up in the base stream (layer 0)

        To handle this, we:
        1. Build a table mapping stack depths to their positions
        2. Skip whitespace (which might cross buffer boundaries)
        3. Return the appropriate position based on where we ended up:
           - If we changed stack depth: return position from the new stack depth
           - If we stayed in same stack: return original position tuple

        Returns:
            Tuple[int, int]: (position, stack_depth) where:
                - position is the index in the relevant buffer or base stream
                - stack_depth indicates which buffer layer we're in (0 for base stream)
        """
        start_pos, start_stack = self.get_pos()
        prev_pos_table: List[Tuple[int, int]] = [super().get_pos()]
        for i, (tokens, idx) in enumerate(self._buffer):
            prev_pos_table.append((idx, i + 1))
        super().skip_whitespace()
        cur_pos, cur_stack = self.get_pos()
        if cur_stack != start_stack:
            return prev_pos_table[cur_stack]
        return (start_pos, start_stack)


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
