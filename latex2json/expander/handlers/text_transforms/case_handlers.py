from enum import Enum
from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


class CaseTransform(Enum):
    UPPERCASE = "uppercase"
    LOWERCASE = "lowercase"

    def transform(self, text: str) -> str:
        return text.upper() if self == CaseTransform.UPPERCASE else text.lower()

    def transform_tokens(self, tokens: List[Token]) -> List[Token]:
        out = []
        for tok in tokens:
            tok = tok.copy()
            if tok.catcode == Catcode.LETTER:
                tok.value = self.transform(tok.value)
            out.append(tok)
        return out


def case_transform_handler(
    expander: ExpanderCore, token: Token, transform_type: CaseTransform
) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tok = expander.peek()
    if tok is None:
        expander.logger.warning(
            f"Warning: \\{transform_type.value} expects args, but None"
        )
        return None
    if tok.type == TokenType.CONTROL_SEQUENCE:
        exp = expander.expand_next()
        if exp:
            expander.push_tokens(exp)
        expander.skip_whitespace()

    # dont expand tokens, \uppercase\lowercase only transforms nonexpanded tokens i.e. letters
    tokens = expander.parse_brace_as_tokens()
    if tokens is None:
        expander.logger.warning(
            f"Warning: \\{transform_type.value} expects a brace-enclosed argument"
        )
        return None

    tokens = transform_type.transform_tokens(tokens)
    expander.push_tokens(tokens)
    return []


def uppercase_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return case_transform_handler(expander, token, CaseTransform.UPPERCASE)


def lowercase_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    return case_transform_handler(expander, token, CaseTransform.LOWERCASE)


def register_case_handlers(expander: ExpanderCore):
    expander.register_handler(r"\uppercase", uppercase_handler, is_global=True)
    expander.register_handler(r"\lowercase", lowercase_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_case_handlers(expander)

    text = r"\uppercase{hello} \lowercase{WORLD}"
    out = expander.expand(text)  # HELLO world

    text = r"""
    \def\foo{foo} 
    \uppercase{\foo bar} % foo BAR (\foo->foo will not be uppercase)
    \uppercase\expandafter{\foo bar} % FOO BAR (foo will be expanded due to expandafter skipping the {, expanding \foo)
    """.strip()
    out = expander.expand(text)
