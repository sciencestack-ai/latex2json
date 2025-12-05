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


def render_math_children_to_json(
    children: List[ASTNode], merge_nodes: bool = True
) -> List[dict]:
    """
    Render math children to JSON, converting CommandNode and nested EquationNode to text.

    Args:
        children: List of child nodes to render
        merge_nodes: Whether to merge text nodes and add spacing (default True)

    Returns:
        List of JSON dictionaries representing the rendered children
    """
    if not merge_nodes:
        # Simplified version for array cells - no copying, just direct conversion
        result = []
        for child in children:
            if isinstance(child, CommandNode):
                result.append({"type": "text", "text": child.detokenize()})
            elif isinstance(child, EquationNode):
                result.append({"type": "text", "text": child.equation_to_str()})
            else:
                result.append(child.to_json())
        return result

    # Full version with merging and spacing for EquationNode
    nodes = []

    def should_add_space_after(i: int) -> bool:
        if i >= len(children) - 1:
            return False
        child = children[i]
        if isinstance(child, CommandNode):
            if not child.name[-1].isalpha():
                return False
        next_node = children[i + 1]
        if isinstance(next_node, TextNode):
            if next_node.text and next_node.text[0].isalpha():
                return True
        return False

    for i, child in enumerate(children):
        styles = child.styles
        labels = child.labels

        if isinstance(child, CommandNode):
            cmd_str = child.detokenize()
            node = TextNode(cmd_str)
            node.add_styles(styles)
            node.labels = labels
            nodes.append(node)
        elif isinstance(child, EquationNode):
            eq_str = child.equation_to_str()
            node = TextNode(eq_str)
            node.add_styles(styles)
            node.labels = labels
            nodes.append(node)
        else:
            nodes.append(child)

        if should_add_space_after(i):
            nodes.append(TextNode(" "))

    nodes = merge_text_nodes(nodes, ignore_styles=True)
    return [node.to_json() for node in nodes]


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

        self.is_math = True

        # # don't postprocess equation nodes
        # self.should_postprocess = False

    def set_body(self, body: List[ASTNode]):
        body = strip_whitespace_nodes(body)
        self.set_children(body)
        # Cache invalidation is handled by set_children

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
        # Check cache first
        if self._json_cache is not None:
            return self._json_cache.copy()

        result = super().to_json()
        result["type"] = NodeTypes.EQUATION
        result["display"] = self.equation_type.value
        if self.equation_type != DisplayType.INLINE:
            result["name"] = self.env_name
        if self.numbering:
            result["numbering"] = self.numbering

        content_json = render_math_children_to_json(self.children, merge_nodes=True)
        result["content"] = content_json

        # Cache the result
        self._json_cache = result.copy()
        return result

    def copy(self):
        return EquationNode(
            math_nodes=self.copy_nodes(self.children),
            env_name=self.env_name,
            equation_type=self.equation_type,
            numbering=self.numbering,
        )


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

        self.is_math = True

        # # don't postprocess equation array nodes
        # self.should_postprocess = False

    def set_children(self, children: List[RowNode]):
        super().set_children(children)
        for row in children:
            row.is_math = True
            # also set is_math for all cells in the row
            for cell in row.cells:
                cell.is_math = True

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
                cell_content = render_math_children_to_json(
                    cell.children, merge_nodes=False
                )
                row_content.append(cell_content)
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

    def copy(self):
        return EquationArrayNode(
            env_name=self.env_name,
            row_nodes=self.copy_nodes(self.row_nodes),
            row_numberings=self.row_numberings.copy() if self.row_numberings else None,
            args_str=self.args_str,
        )
