from latex2json.expander.expander import Expander
from latex2json.tokens.types import EnvironmentStartToken, Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_float_handler():
    expander = Expander()
    # test these are converted to envstart + env end tokens
    text = r"""
\makeatletter
\@float{figure}[htb][ss]
    \caption{FIGURE}
\end@float
\makeatother
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("figure")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="figure")

    # test float env nested inside its own renewenvironment env (ensure no infinite recursion)
    text = r"""
\makeatletter
\renewenvironment{myenv}
  {\@float{myenv}}
  {\end@float}
\makeatother

\begin{myenv}TABLE\end{myenv}
""".strip()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken("myenv")
    assert out[-1] == Token(type=TokenType.ENVIRONMENT_END, value="myenv")
