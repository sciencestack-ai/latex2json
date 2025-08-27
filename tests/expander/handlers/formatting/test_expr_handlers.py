from latex2json.expander.expander import Expander
from latex2json.registers.utils import dimension_to_scaled_points
from latex2json.tokens.utils import strip_whitespace_tokens


def test_numexpr_handler():
    expander = Expander()

    # numexpr ends on EOL or \relax
    text = r"""
    \the\numexpr 1+2 % 3
    4
    """.strip()
    out = expander.expand(text)
    assert out[0] == expander.expand("3")[0]
    assert out[-1] == expander.expand("4")[0]

    # single line numexpr
    out = expander.expand(r"\the\numexpr 1*3+4+(1+1)*2")
    assert out == expander.expand("11")

    # test with def
    # note that \numexpr 1+4 continues to evaluate even after \def
    text = r"""
    \def\xx{\the\numexpr 1+4}
    \xx +33 % becomes 1+4+33 = 38
    11
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[:2] == expander.expand("38")
    assert out[-2:] == expander.expand("11")

    # edge case: check that unbalanced parentheses still evaluate
    text = r"""
    \def\xx{1+4}
    \def\xx{1+4 \relax} % relax token stops numexpr eval, leaving only 1+4 = 5
    \the\numexpr (\xx*3+(1+3)) * 3
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    # thus, '\numexpr (\xx' becomes 5
    assert out == expander.expand("5*3+(1+3)) * 3")

    # test with counters/registers e.g. \value
    text = r"""
\setcounter{section}{3}
\def\xx{\the\numexpr \value{section} + \value{section} * \value{section}}
\xx
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == expander.expand("%d" % (3 + 3 * 3))


def test_dimexpr_handler():
    expander = Expander()

    text = r"""
\the\dimexpr 1pt * 10\relax
    """.strip()
    out = expander.expand(text)
    dim_points = dimension_to_scaled_points(1, "pt") * 10
    assert out == expander.expand(str(dim_points))

    # test can be used with registers
    text = r"""
    \setbox0=\hbox{1pt}
    \setbox1=\hbox{1pt}
    \wd0=15pt
    \wd1=10pt
    \the\dimexpr \wd0 + \wd1 \relax
    """.strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    dim_points = dimension_to_scaled_points(25, "pt")
    assert out == expander.expand(str(dim_points))


def test_glueexpr_handler():
    expander = Expander()

    r"""
https://tex.stackexchange.com/questions/245635/formal-syntax-rules-of-dimexpr-numexpr-glueexpr

In glue expressions the plus/minus parts do not need parenthesis to be affected by a factor as they are necessarily one entity. So for example
\the\glueexpr 5pt plus 1pt * 2 \relax
yields 10pt plus 2pt i.e. 12pt
    """

    text = r"""
\the\glueexpr 5pt plus 1pt * 2 \relax
    """.strip()
    out = expander.expand(text)
    dim_points = dimension_to_scaled_points(12, "pt")
    assert out == expander.expand(str(dim_points))
