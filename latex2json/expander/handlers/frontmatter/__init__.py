from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.frontmatter.maketitle import (
    register_maketitle_handlers,
)


def register_frontmatter_handlers(expander: ExpanderCore):
    register_maketitle_handlers(expander)
