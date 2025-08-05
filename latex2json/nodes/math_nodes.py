from typing import List, Optional
from latex2json.nodes.base_nodes import (
    ASTNode,
    DisplayType,
    check_asts_equal,
    CommandNode,
    TextNode,
)

from latex2json.nodes.tabular_node import RowNode
from latex2json.nodes.utils import merge_text_nodes, strip_whitespace_nodes
from latex2json.nodes.node_types import NodeTypes


def strip_balanced_braces(text: str) -> str:
    # Strip balanced braces from start/end using stack matching
    while text and text.startswith("{"):
        # Check if braces are balanced and match at start/end
        stack = []
        balanced = True
        should_strip = False

        for i, char in enumerate(text):
            if char == "{":
                stack.append(i)
            elif char == "}":
                if not stack:
                    balanced = False
                    break
                start_pos = stack.pop()
                # If this is the closing brace and matches opening,
                # and there are no other unmatched braces
                if not stack and i == len(text) - 1 and start_pos == 0:
                    should_strip = True

        # Only continue if we found a matching pair to strip
        if not balanced or not should_strip:
            break

        text = text[1:-1]

    return text


class EquationNode(ASTNode):
    def __init__(
        self,
        math_nodes: List[ASTNode],
        env_name: str = "equation",
        equation_type: DisplayType = DisplayType.INLINE,
        numbering: Optional[str] = None,
    ):
        super().__init__()
        self.numbering = numbering
        self.equation_type = equation_type
        self.env_name = env_name

        self.set_body(math_nodes)

        # don't postprocess equation nodes
        self.should_postprocess = False

    def set_body(self, body: List[ASTNode]):
        body = strip_whitespace_nodes(body)
        self.set_children(body)

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def __str__(self):
        return self.detokenize() + (f" ({self.numbering})" if self.numbering else "")

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EquationNode):
            return False
        if self.equation_type != other.equation_type:
            return False
        if self.numbering != other.numbering:
            return False
        if self.env_name != other.env_name:
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

        if (
            self.equation_type == DisplayType.BLOCK
            and self.env_name == "equation"
            and not self.numbering
        ):
            return "$$" + math_str + "$$"

        env_name = self.env_name
        begin_str = f"\\begin{{{env_name}}}\n"
        end_str = f"\n\\end{{{env_name}}}"
        return begin_str + math_str + end_str

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.EQUATION
        result["display"] = self.equation_type.value
        if self.equation_type != DisplayType.INLINE:
            result["name"] = self.env_name
        if self.numbering:
            result["numbering"] = self.numbering

        # convert command nodes to text nodes
        nodes = []
        childs = self.children

        def should_add_space_after(i: int) -> bool:
            # if we're converting to a string, we need to be careful about textnodes rightafter commands
            # so we add a space after the command

            if i >= len(childs) - 1:
                return False

            child = childs[i]
            if isinstance(child, CommandNode):
                if not child.name[-1].isalpha():
                    return False
            next_node = childs[i + 1]
            if isinstance(next_node, TextNode):
                if next_node.text and next_node.text[0].isalpha():
                    return True
            return False

        for i, child in enumerate(childs):
            node = child
            styles = child.styles
            if isinstance(child, CommandNode):
                cmd_str = child.detokenize()
                node = TextNode(cmd_str)
            elif isinstance(child, EquationNode):
                eq_str = child.equation_to_str()
                # if an inner equation node, convert the equation str (without $$) to text node
                node = TextNode(eq_str)
            elif isinstance(child, EquationArrayNode):
                # if an inner equation array node that is not numbered
                # and is all text and commands, i.e. no special nodes like \ref \cite \envs
                # convert the equation array str to text node
                if child.is_all_text_and_commands() and not child.has_numbering():
                    node = TextNode(child.detokenize())
            else:
                node = child.copy()
            node.add_styles(styles)
            nodes.append(node)
            if should_add_space_after(i):
                nodes.append(TextNode(" "))
        nodes = merge_text_nodes(nodes, ignore_styles=True)
        content_json = [node.to_json() for node in nodes]

        result["content"] = content_json

        return result


class EquationArrayNode(ASTNode):
    def __init__(
        self,
        env_name: str,  # can be "align", "array", "matrix", etc
        row_nodes: List[RowNode] = [],
        row_numberings: Optional[List[Optional[str]]] = None,
        args_str: Optional[List[str]] = None,  # e.g. ["l"] if \begin{array}{l}
    ):
        super().__init__()
        self.env_name = env_name
        self.row_numberings = row_numberings
        self.args_str = args_str
        self.set_children(row_nodes)

        # don't postprocess equation array nodes
        self.should_postprocess = False

    @property
    def row_nodes(self) -> List[RowNode]:
        return self.children

    def has_numbering(self) -> bool:
        return self.row_numberings is not None and any(
            numbering is not None for numbering in self.row_numberings
        )

    def is_all_text_and_commands(self) -> bool:
        for row in self.row_nodes:
            for cell in row.cells:
                for child in cell.children:
                    if not isinstance(child, (TextNode, CommandNode)):
                        return False
        return True

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EquationArrayNode):
            return False
        if self.row_numberings != other.row_numberings:
            return False
        if self.env_name != other.env_name:
            return False
        return all(a == b for a, b in zip(self.children, other.children))

    def detokenize(self, add_numbering: bool = False) -> str:
        """Convert the equation array node back to LaTeX source code."""
        args_str = ""
        if self.args_str:
            for i, arg in enumerate(self.args_str):
                args_str += "{" + arg + "}"

        out = f"\\begin{{{self.env_name}}}{args_str}\n"

        for i, row in enumerate(self.row_nodes):
            out += row.detokenize()
            if (
                add_numbering
                and self.row_numberings
                and 0 <= i < len(self.row_numberings)
            ):
                out += f" ({self.row_numberings[i]})"
            if i < len(self.row_nodes) - 1:
                out += " \\\\\n"

        out += f"\n\\end{{{self.env_name}}}"
        return out

    def __str__(self):
        out_str = self.detokenize(add_numbering=True)
        return out_str

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.EQUATION_ARRAY
        result["name"] = self.env_name
        if self.args_str:
            result["args"] = self.args_str.copy()

        content = []
        for i, row in enumerate(self.row_nodes):
            row_json = row.to_json()
            row_content = []

            for cell in row.cells:
                # convert each cell to equation node to ensure json output consistency
                eq_node = EquationNode(cell.children)
                eq_node_json = eq_node.to_json()
                row_content.append(eq_node_json["content"])
            row_json["content"] = row_content

            if (
                self.row_numberings
                and 0 <= i < len(self.row_numberings)
                and self.row_numberings[i]
            ):
                row_json["numbering"] = self.row_numberings[i]
            content.append(row_json)
        result["content"] = content
        return result
