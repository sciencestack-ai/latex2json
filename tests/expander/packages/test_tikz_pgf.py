from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_tikz():
    expander = Expander()

    tikz_cmd = r"\fill[natural] (0,0) circle (.5ex);"
    short_ver = r"\tikz" + tikz_cmd
    long_ver = r"""\begin{tikzpicture}%s\end{tikzpicture}""" % (tikz_cmd)
    out = expander.expand(short_ver)
    out2 = expander.expand(long_ver)
    assert out == out2

    # test with braces
    text = r"""
\tikz[baseline=(A.base)]{%s}
""" % (
        tikz_cmd
    )
    out = expander.expand(text.strip())
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\begin{tikzpicture}[baseline=(A.base)]{%s}\end{tikzpicture}" % (
        tikz_cmd
    )
