from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens.types import Token


def register_titling(expander: ExpanderCore):
    # ignore for now?
    ignore_patterns = {
        "pretitle": 1,
        "posttitle": 1,
        "preauthor": 1,
        "postauthor": 1,
        "predate": 1,
        "postdate": 1,
    }

    register_ignore_handlers_util(expander, ignore_patterns)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_titling(expander)

    out = expander.expand(r"\pretitle{Hello} \posttitle{World}")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""
