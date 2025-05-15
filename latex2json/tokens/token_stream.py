from collections import deque
from typing import Deque, Optional

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_whitespace_token


# Dynamic token stream
class TokenStream:
    """A stream of Tokens, fetching dynamically from a Tokenizer and skipping ignored tokens."""

    def __init__(self, tokenizer: Tokenizer):
        self.tokenizer = tokenizer

    @property
    def pos(self) -> int:
        return self.tokenizer.pos

    def set_pos(self, pos: int):
        self.tokenizer.pos = pos

    def set_text(self, text: str):
        self.tokenizer.set(text)

    def reset(self):
        self.set_pos(0)

    def peek(self, n: int = 0) -> Optional[Token]:
        """Peek at the token at the given offset from the current position."""
        start_pos = self.pos
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
        return self.tokenizer.eof()

    def skip_whitespace(self) -> int:
        """Consume all consecutive CHARACTER tokens with Catcode.SPACE.
        Returns the start position pre skip
        """
        start_pos = self.pos
        while not self.eof():
            next_token = self.peek()
            if not next_token or is_whitespace_token(next_token):
                self.consume()
            else:
                break
        return start_pos


if __name__ == "__main__":
    tokenizer = Tokenizer()
    stream = TokenStream(tokenizer)
    tokenizer.set("Hello, world!")
    print(stream.consume())
