from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util
from latex2json.tokens import Token


def two_column_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    out_tokens = expander.parse_bracket_as_tokens(expand=True)
    return out_tokens


def texorpdfstring_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2, expand=True)
    if len(blocks) != 2:
        expander.logger.warning("Expected 2 blocks for \\texorpdfstring")
        return []
    # choose the second block
    return blocks[1]


def head_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    expander.parse_bracket_as_tokens(expand=True)
    expander.skip_whitespace()
    out_tokens = expander.parse_brace_as_tokens(expand=True)
    return out_tokens


def register_layout_content_handlers(expander: ExpanderCore):
    # columns
    expander.register_handler("onecolumn", lambda expander, token: [], is_global=True)
    expander.register_handler("twocolumn", two_column_handler, is_global=True)
    # texorpdfstring
    expander.register_handler("texorpdfstring", texorpdfstring_handler, is_global=True)

    # fancyhead/headers
    for head in ["fancyhead", "fancyheadoffset", "rhead", "chead", "lhead"]:
        expander.register_handler(head, head_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_layout_content_handlers(expander)
