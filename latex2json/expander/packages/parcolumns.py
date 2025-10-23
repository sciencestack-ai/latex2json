from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.latex_maps.environments import LIST_ENVIRONMENTS, EnvironmentDefinition
from latex2json.tokens.types import EnvironmentType, Token


def colchunk_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    column_tokens = expander.parse_brace_as_tokens(expand=True)
    return column_tokens


def register_parcolumns(expander: ExpanderCore):
    expander.register_handler("colchunk", colchunk_handler, is_global=True)

    ignore_patterns = {"colplacechunks": 0}
    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_parcolumns(expander)

    text = r"""

\begin{parcolumns}[rulebetween]{2}
  \colchunk{Left column text}
  \colchunk{Right column text}
  \colplacechunks % align them in one row
\end{parcolumns}
""".strip()
    out = expander.expand(text)
