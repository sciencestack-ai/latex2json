import logging
from typing import Optional
from latex2json.parser.parser_core import ParserCore


class Parser(ParserCore):
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)

        self._register_handlers()

    def _register_handlers(self):
        from latex2json.parser.handlers import register_handlers

        register_handlers(self)


if __name__ == "__main__":
    from latex2json.nodes.syntactic_nodes import strip_whitespace_nodes

    text = r"""
    \textbf{ \textit {NODE} }

    \section{Hello}
    \label{hello}
    """

    parser = Parser()
    parser.set_text(text)
    out = parser.parse()
    out = strip_whitespace_nodes(out)
    print(out)
    # out = parser.expander.expand(text)
