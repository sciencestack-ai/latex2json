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
    \begin{align} \label{eq:1}
    1+1
    \end{align}

    \begin{table}
    \caption{CAPTION}
    \label{tab:1}
    \end{table}

    \label{WUT}
    """

    parser = Parser()
    parser.set_text(text)
    out = parser.parse()
    out = strip_whitespace_nodes(out)
    out = [node for node in out if not is_whitespace_node(node)]
    for node in out:
        node_meta_str = f"STYLES: {node.styles}"
        if node.labels:
            node_meta_str += f", LABELS: {node.labels}"
        print(node, f"-> {node_meta_str}")
    # out = parser.expander.expand(text)
