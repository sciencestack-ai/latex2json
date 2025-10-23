from latex2json.expander.expander import Expander
from latex2json.tokens.types import (
    EnvironmentEndToken,
    EnvironmentStartToken,
    Token,
    TokenType,
)


def test_parcolumns():
    expander = Expander()

    text = r"""
\begin{parcolumns}[rulebetween]{2}
  \colchunk{Left column text}
  \colchunk{Right column text}
  \colplacechunks % align them in one row
\end{parcolumns}
""".strip()
    out = expander.expand(text)

    assert out[0] == EnvironmentStartToken("parcolumns")
    assert out[-1] == EnvironmentEndToken("parcolumns")
    column_str = expander.convert_tokens_to_str(out[1:-1]).strip()
    columns = [column.strip() for column in column_str.split("\n")]
    assert columns == ["Left column text", "Right column text"]
