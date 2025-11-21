from typing import List, Optional
from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import END_BRACE_TOKEN, Token, TokenType
from latex2json.tokens.types import BEGIN_BRACE_TOKEN


def detokenize_handler(expander: ExpanderCore, token: Token) -> Optional[List[Token]]:
    expander.skip_whitespace()
    tokens = expander.parse_brace_as_tokens(verbatim=True, expand=False)

    if not tokens:
        return []

    for tok in tokens:
        if tok.catcode != Catcode.SPACE:
            tok.catcode = Catcode.OTHER

    return tokens


def register_detokenize_handler(expander: ExpanderCore):
    expander.register_handler("detokenize", detokenize_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    text = r"""
\detokenize{https://www.wolframalpha.com/input?i=expand+42*d*%28d-1%29%5E2+-+288*binomial%28d%2C4%29+%2B+29*binomial%28d-1%2C2%29%5E2+%2B+203*binomial%28d-1%2C2%29+%2B+504+-294%28d%5E2-d%29}
HAHA
""".strip()
    out = expander.expand(text)
