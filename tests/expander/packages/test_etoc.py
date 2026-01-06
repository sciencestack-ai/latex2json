from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_epsfig():
    expander = Expander()

    text = r"""
\etocdepthtag.toc{sdsd}
\etocimmediatedepthtag.toc{sdsd}
\etocsettagdepth{sdsd}{3}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""
