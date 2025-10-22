from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    EnvironmentEndToken,
    EnvironmentStartToken,
    EnvironmentType,
)
from latex2json.tokens.utils import strip_whitespace_tokens


def test_newlist():
    text = r"""

\newlist{inlinelist}{itemize*}{1}
\setlist[inlinelist,1]{label=(\roman*)} % ignored
\begin{inlinelist}
    \item Item 1
    \item Item 2
\end{inlinelist}
""".strip()

    expander = Expander()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out[0] == EnvironmentStartToken(
        "itemize*", numbering=None, env_type=EnvironmentType.LIST
    )
    assert out[-1] == EnvironmentEndToken("itemize*")
