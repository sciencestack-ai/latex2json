from latex2json.expander.expander_core import ExpanderCore


def register_other_primitives(expander: ExpanderCore):
    """
    Register LaTeX primitive macros defined via ltx_text.
    Consolidates simple macro definitions that don't require Python handlers.
    """

    # @firstofone, @firstoftwo, @secondoftwo
    ltx_text_at_x_of_x = r"""
\long\def\@firstofone#1{#1}
\long\def\@firstoftwo#1#2{#1}
\long\def\@secondoftwo#1#2{#2}
"""
    expander.expand_ltx(ltx_text_at_x_of_x)

    # @dblarg, @xdblarg
    ltx_text_dblarg = r"""
\long\def\@dblarg#1{\@ifnextchar[{#1}{\@xdblarg{#1}}}
\long\def\@xdblarg#1#2{#1[{#2}]{#2}}
"""
    expander.expand_ltx(ltx_text_dblarg)

    # @addpunct
    #     ltx_addpunct = r"""
    # \def\@addpunct#1{%
    #   \futurelet\@let@token\@addpunct@i #1%
    # }

    # \def\@addpunct@i#1{%
    #   \ifx\@let@token.%
    #     \if.#1\else#1\fi
    #   \else
    #     #1%
    #   \fi
    # }
    # """
    ltx_addpunct = r"""
    \def\@addpunct#1{#1} % just keep it simple??..
"""
    expander.expand_ltx(ltx_addpunct)
