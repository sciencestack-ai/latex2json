from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.nodes.base import ASTNode
from latex2json.parser.parser_core import ParserCore


class Expander(ExpanderCore):
    def __init__(self, parser: ParserCore = ParserCore()):
        super().__init__(parser)

        self._init_primitives()

    def _init_primitives(self):
        # Define core TeX/LaTeX primitives in the base registry.
        # Primitives are defined using define_primitive which uses set(is_global=True)
        from latex2json.expander.handlers import register_handlers

        register_handlers(self)


if __name__ == "__main__":
    expander = Expander()

    text = r"""
    {
            \edef\bar{NEW BAR}
            \edef\barry{BARRY}
    }
""".strip()
    expander.set_text(text)
    print(expander.process())
