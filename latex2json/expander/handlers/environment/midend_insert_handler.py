from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def midinsert_handler(expander: ExpanderCore, token: Token):
    expander.push_text(r"\begin{figure}[h]")
    return []


def topinsert_handler(expander: ExpanderCore, token: Token):
    expander.push_text(r"\begin{figure}[t]")
    return []


def pageinsert_handler(expander: ExpanderCore, token: Token):
    expander.push_text(r"\begin{figure}[p]")
    return []


def endinsert_handler(expander: ExpanderCore, token: Token):
    expander.push_text(r"\end{figure}")
    return []


def register_midend_insert_handler(expander: ExpanderCore):
    expander.register_handler("\\midinsert", midinsert_handler, is_global=True)

    expander.register_handler("\\topinsert", topinsert_handler, is_global=True)

    expander.register_handler("\\pageinsert", pageinsert_handler, is_global=True)

    expander.register_handler("\\endinsert", endinsert_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_midend_insert_handler(expander)
    text = r"""
\midinsert
\endinsert
""".strip()
    out = expander.expand(text)
    print(out)
