from typing import List, Optional
from latex2json.nodes.base_nodes import (
    ASTNode,
    DisplayType,
    check_asts_equal,
    CommandNode,
    TextNode,
)

from latex2json.nodes.utils import strip_whitespace_nodes


class EquationNode(ASTNode):
    def __init__(
        self,
        math_nodes: List[ASTNode],
        equation_type: DisplayType = DisplayType.INLINE,
        numbering: Optional[str] = None,
    ):
        super().__init__()
        self.numbering = numbering
        self.equation_type = equation_type

        self.set_body(math_nodes)

    def set_body(self, body: List[ASTNode]):
        body = strip_whitespace_nodes(body)
        self.set_children(body)

    def __str__(self):
        return self.detokenize() + (f" ({self.numbering})" if self.numbering else "")

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EquationNode):
            return False
        if self.equation_type != other.equation_type:
            return False
        if self.numbering != other.numbering:
            return False
        return check_asts_equal(self.children, other.children)

    def equation_to_str(self):
        eq_str = ""
        N = len(self.children)

        prev_node = None
        # if we're converting to a string, we need to be careful about textnodes rightafter commands
        for i, node in enumerate(self.children):
            if isinstance(node, TextNode) and isinstance(prev_node, CommandNode):
                if node.text and node.text[0].isalpha():
                    eq_str += " "
            eq_str += node.detokenize()
            prev_node = node
        return eq_str

    def detokenize(self):
        math_str = self.equation_to_str()
        if self.equation_type == DisplayType.INLINE:
            return "$" + math_str + "$"

        if self.equation_type == DisplayType.DISPLAY and not self.numbering:
            return "$$" + math_str + "$$"

        env_name = "align" if self.equation_type == DisplayType.ALIGN else "equation"
        if not self.numbering:
            env_name += "*"
        begin_str = f"\\begin{{{env_name}}}"
        end_str = f"\\end{{{env_name}}}"
        return begin_str + math_str + end_str

    def to_json(self):
        result = super().to_json()
        result["type"] = "equation"
        result["content"] = [child.to_json() for child in self.children]
        result["display"] = self.equation_type.value
        if self.numbering:
            result["numbering"] = self.numbering
        return result
