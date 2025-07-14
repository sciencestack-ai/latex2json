from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.if_else.base_if import IfMacro


def register_if_format_handlers(expander: ExpanderCore):

    LATEX_INTERNAL_IFS = {
        "if@twoside": False,
        "if@titlepage": False,
        "if@openright": False,
        "if@mainmatter": False,
        "if@restonecol": False,
        "if@inlabel": False,
        "if@inbib": False,
        "if@filesw": False,
        "if@tempswa": False,
        "if@newlist": False,
    }

    # iftrue + iffalse
    for name, condition in LATEX_INTERNAL_IFS.items():
        expander.register_macro(
            name,
            IfMacro(name, lambda expander, token: (condition, None)),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_if_format_handlers(expander)
    text = r"""
\makeatletter
\if@twoside TWOSIDE
\else NOT TWOSIDE \fi
"""

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
