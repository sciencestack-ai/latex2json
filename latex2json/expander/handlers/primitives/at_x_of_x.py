from latex2json.expander.expander_core import ExpanderCore


def register_at_x_of_x_handlers(expander: ExpanderCore):
    # ensure \def primitives have been registered before this!

    ltx_text = r"""
\long\def\@firstofone#1{#1}
\long\def\@firstoftwo#1#2{#1}
\long\def\@secondoftwo#1#2{#2}
"""
    expander.expand_ltx(ltx_text)
