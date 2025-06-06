from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token


def cref_handler(expander: ExpanderCore, token: Token):
    pass


def register_cleveref(expander: ExpanderCore):
    for cref in ["cref", "Cref"]:
        expander.register_handler(cref, cref_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_cleveref(expander)
    print(expander.expand(r"\cref{fig:myfig}"))
