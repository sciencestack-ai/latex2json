from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import wrap_tokens_in_braces


def register_other_packages(expander: ExpanderCore):
    """
    Register LaTeX package macros defined via ltx_text.
    Consolidates simple macro definitions that don't require complex Python handlers.
    """

    # Register xcolor handler (has Python logic)

    # xcolor package macros
    ltx_text_xcolor = r"""
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
    expander.expand_ltx(ltx_text_xcolor)
