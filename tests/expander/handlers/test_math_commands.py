from latex2json.expander.expander import Expander


def test_math_command_handlers():
    expander = Expander()

    text = r"""
\newcommand{\xxx}[2]{\frac#1#2}
\def\aaa{A+B}
$\xxx\aaa3$
"""
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"$\frac{A+B}{3}$"

    text = r"""
    \newcommand{\ti}{\tilde}
    \newcommand{\calR}{\mathcal R}
    $\ti\calR$
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"$\tilde{\mathcal{R}}$"
