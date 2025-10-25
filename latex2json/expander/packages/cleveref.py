from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token


# def cref_handler(expander: ExpanderCore, token: Token):
#     pass


# def crefname_handler(expander: ExpanderCore, token: Token):
#     pass


def register_cleveref(expander: ExpanderCore):
    # for cref in ["cref", "Cref"]:
    #     expander.register_handler(cref, cref_handler, is_global=True)

    # for crefname in ["crefname", "Crefname"]:
    #     expander.register_handler(crefname, crefname_handler, is_global=True)

    ignore_patterns = {
        "crefname": 3,
        "Crefname": 3,
        "crefformat": 2,
    }

    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_cleveref(expander)
    print(expander.expand(r"\crefname{figure}{Figure}{Figures}"))
