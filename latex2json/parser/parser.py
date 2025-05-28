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
    from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes

    text = r"""
    \textbf{ \textit {NODE} }

    \textbf{ \section{Hello} }
    \label{hello}
    { \bf 
        BOLD
        { \it
            BOLD ITALIC
        }
    }
    """

    text = r"""
    \bf 
    \begin{align}
    1+1
    \end{align}
"""

    parser = Parser()
    parser.set_text(text)
    out = parser.parse()
    out = strip_whitespace_nodes(out)
    out = [node for node in out if not is_whitespace_node(node)]
    for node in out:
        print(node, "->", node.styles)
    # out = parser.expander.expand(text)
