from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.latex_maps.environments import LIST_ENVIRONMENTS, EnvironmentDefinition
from latex2json.tokens.types import EnvironmentType, Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def color_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    # invoke internal @color command
    color_tokens = expander.parse_brace_as_tokens(expand=True)
    if not color_tokens:
        return []
    expander.expand_tokens([Token(TokenType.CONTROL_SEQUENCE, "@color"), *color_tokens])
    # return as raw \color for downstream handling e.g. parser
    return [
        Token(TokenType.CONTROL_SEQUENCE, "color"),
        *wrap_tokens_in_braces(color_tokens),
    ]


def register_xcolor(expander: ExpanderCore):
    expander.register_handler("color", color_handler, is_global=True)

    # ensure \def is registered
    ltx_text = r"""
\def\default@color{black}          % The "normal" text color
\let\current@color\default@color   % Initialize current color to default

%%---------------------------------------------
%% Low-level group wrappers
%%---------------------------------------------
\def\color@begingroup{%
  \begingroup
  \set@color
}

\def\color@endgroup{%
  \endgroup
}

%%---------------------------------------------
%% Internal state setter
%%---------------------------------------------
\def\set@color{%
  \ifx\current@color\default@color
    % If we are at the default color, no change needed
  \else
    \expandafter\color@setgroup\current@color\@nil
  \fi
}

%%---------------------------------------------
%% The internal color setter
%%---------------------------------------------
\def\@color#1{%
  \edef\current@color{#1}% store color spec
  \set@color             % activate it
}
"""
    expander.expand_ltx(ltx_text)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_xcolor(expander)

    text = r"""
    \makeatletter
\color@begingroup
HAHA
\color@endgroup
""".strip()
    out = expander.expand(text)
