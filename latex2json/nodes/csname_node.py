from typing import Any, List

from latex2json.nodes.base import ASTNode, check_asts_equal
from latex2json.nodes.syntactic_nodes import CommandNode, TextNode


class CSNameNode(ASTNode):
    def __init__(self, nodes: List[ASTNode]):
        self.nodes = nodes
        self.set_children(nodes)

    def get_literal(self):
        out_str = "\\csname"
        for node in self.nodes:
            if isinstance(node, TextNode):
                out_str += node.text
            elif isinstance(node, CommandNode):
                out_str += node.name

        out_str += "\\endcsname"
        return out_str

    def get_collapsed_literal(self):
        out_str = ""
        for node in self.nodes:
            if isinstance(node, TextNode):
                out_str += node.text
            elif isinstance(node, CommandNode):
                out_str += node.name

        return out_str.replace(" ", "")

    def __str__(self):
        return f"\\csname({self.nodes})\\endcsname"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CSNameNode):
            return False
        return check_asts_equal(self.nodes, other.nodes)

    def detokenize(self):
        return self.get_literal()
