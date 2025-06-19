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
        self.body = strip_whitespace_nodes(body)
        self.set_children(self.body)

    @property
    def math_nodes(self):
        return self.body

    def __str__(self):
        return self.detokenize() + (f" ({self.numbering})" if self.numbering else "")

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EquationNode):
            return False
        if self.equation_type != other.equation_type:
            return False
        if self.numbering != other.numbering:
            return False
        return check_asts_equal(self.math_nodes, other.math_nodes)

    def equation_to_str(self):
        eq_str = ""
        N = len(self.math_nodes)

        prev_node = None
        # if we're converting to a string, we need to be careful about textnodes rightafter commands
        for i, node in enumerate(self.math_nodes):
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


# class DisplayEquationNode(ASTNode):
#     def __init__(self, text: str, align=False, numbering: Optional[str] = None):
#         self.text = text
#         self.align = align
#         self.numbering = numbering

#     def __str__(self):
#         return f"Equation({self.text})"

#     def __eq__(self, other: ASTNode):
#         if not isinstance(other, DisplayEquationNode):
#             return False
#         return (
#             self.text == other.text
#             and self.align == other.align
#             and self.numbering == other.numbering
#         )

#     def detokenize(self):
#         name = "align" if self.align else "equation"
#         if self.numbering is not None:
#             name += f"({self.numbering})"
#         out = f"\\begin{{{name}}}{self.text}\\end{{{name}}}"
#         return out
