"""Common type aliases for the expander package."""

from typing import List, Optional

from latex2json.tokens import Token

TokenResult = Optional[List[Token]]
TokenList = List[Token]
