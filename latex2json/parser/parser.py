import logging
from typing import List, Optional
import re
from latex2json.nodes.base_nodes import ASTNode, CommandNode, NewLineNode, TextNode
from latex2json.nodes.utils import merge_text_nodes
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.catcodes import DEFAULT_CATCODES, Catcode


def normalize_whitespace_and_lines(text: str) -> str:
    # Step 1: Replace two or more newlines (with optional surrounding spaces) with a unique marker.
    # This marker should be something unlikely to appear in your text.
    marker = "<PARA_BREAK>"
    text = re.sub(r"(?:[ \t]*\n[ \t]*){2,}", marker, text)

    # Step 2: Replace any remaining single newline (with optional surrounding spaces) with a single space.
    text = re.sub(r"[ \t]*\n[ \t]*", " ", text)

    # Step 3: Collapse multiple spaces into a single space.
    text = re.sub(r"[ \t]+", " ", text)

    # Step 4: Replace the marker with an actual newline (or any delimiter you prefer).
    text = text.replace(marker, "\n")

    # Optionally, trim leading and trailing whitespace.
    return text  # .strip()


class Parser(ParserCore):
    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__(logger)

        self._register_handlers()

    def _register_handlers(self):
        from latex2json.parser.handlers import register_handlers

        register_handlers(self)

    # override
    def parse(self, text: Optional[str] = None) -> List[ASTNode]:
        nodes = super().parse(text)
        return nodes  # self.postprocess_nodes(nodes)

    def postprocess_nodes(self, nodes: List[ASTNode]) -> List[ASTNode]:
        r"""
        post process nodes by
        1. merging spacing, newlines
        2. handling special characters e.g. ~, \& to text
        """
        final_nodes: List[ASTNode] = []
        for node in nodes:
            replacement_node: Optional[ASTNode] = None
            if isinstance(node, CommandNode):
                name = node.name
                if name == "space":
                    replacement_node = TextNode(" ")
                elif name == "newline":
                    replacement_node = TextNode("\n")
                elif (
                    len(name) == 1 and DEFAULT_CATCODES.get(ord(name)) != Catcode.LETTER
                ):
                    # e.g. \& -> &, \# -> #
                    replacement_node = TextNode(name)
            elif isinstance(node, NewLineNode):
                replacement_node = TextNode("\n")

            if replacement_node:
                replacement_node.add_styles(node.styles)
                final_nodes.append(replacement_node)
                continue

            if isinstance(node, TextNode):
                text = node.text
                # collapse multiple spaces into single space (latex)
                text = normalize_whitespace_and_lines(text)
                node.text = text.replace("~", " ")
            elif node.children:
                node.set_children(self.postprocess_nodes(node.children))

            final_nodes.append(node)

        # then do a final merge of text nodes
        return merge_text_nodes(final_nodes)


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

    \bf
    \hyperref[tab:1]{TABLE}
    \\

    \begin{longtable*}{c|c|c}
     1 & 2 & & 3 \\ 
     \multicolumn{3}{|c|{xxx}}{\multirow{2}{*}{4}} STEP & 6 \\
     abc \\ 
     bbb
    \end{longtable*}

    \begin{generic}
    \end{generic}
    """

    text = r"""
    Hi there~~     bro \& \#
""".strip()

    parser = Parser()
    parser.set_text(text)
    out = parser.parse()
    out = parser.postprocess_nodes(out)
    # out = strip_whitespace_nodes(out)
    # out = [node for node in out if not is_whitespace_node(node)]
    # for node in out:
    #     node_meta_str = f"STYLES: {node.styles}"
    #     if node.labels:
    #         node_meta_str += f", LABELS: {node.labels}"
    #     print(node, f"-> {node_meta_str}")
    # out = parser.expander.expand(text)
