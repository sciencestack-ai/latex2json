from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_newtcbox():
    expander = Expander()

    # rolls out to \tcbox[hello, title=default]{BOX}
    text = r"""
\newtcbox{\mymath}[1][default]{hello, title=#1}

    \mymath{BOX}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\tcbox[hello, title=default]{BOX}"
