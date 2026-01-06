from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token


def etocdepthtag_handler(expander: ExpanderCore, token: Token):
    # ignore: we need to manually parse .toc{...}
    expander.parse_keyword(".toc")
    expander.skip_whitespace()
    expander.parse_brace_as_tokens(expand=False)
    return []


def register_etoc(expander: ExpanderCore):
    for cmd in [
        "etocdepthtag",
        "etocimmediatedepthtag",
        "etocsetlocaltop",
        "etocimmediatesetlocaltop",
    ]:
        expander.register_handler(cmd, etocdepthtag_handler, is_global=True)

    ignore_patterns = {
        "etocsettagdepth": 2,
        "etocclasstocstyle": 0,
        "etoclocaltocstyle": 0,
        "etocobeytoctocdepth": 0,
        "etocobeydepthtags": 0,
        "etocdefaultlines": 0,
        "etocstandardlines": 0,
        "invisibletableofcontents": 0,
        "invisiblelocaltableofcontents": 0,
        "etocobeydepthtags": 0,
        "etocignoredepthtags": 0,
    }
    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_etoc(expander)

    text = r"""
\etocdepthtag.toc{sdsd}
\etocimmediatedepthtag.toc{sdsd}
\etocsettagdepth{sdsd}{3}
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    print(out_str)
