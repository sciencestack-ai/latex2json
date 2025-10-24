from latex2json.expander.expander_core import ExpanderCore


def register_dblarg_handlers(expander: ExpanderCore):
    # ensure \def primitives have been registered before this!

    ltx_text = r"""
    \makeatletter
\long\def\@dblarg#1{\@ifnextchar[{#1}{\@xdblarg{#1}}}
\long\def\@xdblarg#1#2{#1[{#2}]{#2}}
\makeatother
"""
    expander.expand(ltx_text)
