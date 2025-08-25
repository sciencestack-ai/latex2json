from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_epsfig():
    expander = Expander()

    text = r"""
    \epsfxsize=1000pt
    \epsfig{file=eee.eps,other=opts}
    \epsfbox{aaa.eps}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    out_str = out_str.replace(" ", "").replace("\n", "")
    assert out_str == r"\includegraphics{eee.eps}\includegraphics{aaa.eps}"
