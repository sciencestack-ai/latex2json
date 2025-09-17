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
