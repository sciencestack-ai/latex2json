from typing import List
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.node_types import NodeTypes


class MetadataNode(ASTNode):
    def __init__(self, name: str, body: List[ASTNode]):
        super().__init__()
        self.name = name
        self.set_children(body)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, MetadataNode):
            return False
        return check_asts_equal(self.children, other.children)

    def detokenize(self) -> str:
        """Convert the metadata node back to LaTeX source code."""
        content = "".join(child.detokenize() for child in self.children)
        return f"\\{self.name}{{{content}}}"

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = self.name
        if self.children:
            result["content"] = [child.to_json() for child in self.children]
        return result

    def copy(self):
        return MetadataNode(self.name, self.copy_nodes(self.children))


class MaketitleNode(ASTNode):
    """Node representing the output of \\maketitle command.

    Contains frontmatter metadata nodes (title, author, date, etc.) as children.
    This node ensures frontmatter is processed in isolation from the document body.
    """

    def __init__(self, children: List[ASTNode]):
        super().__init__()
        self.set_children(children)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, MaketitleNode):
            return False
        return check_asts_equal(self.children, other.children)

    def detokenize(self) -> str:
        """Convert the maketitle node back to LaTeX source code."""
        return "".join(child.detokenize() for child in self.children)

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.MAKETITLE
        if self.children:
            result["content"] = [child.to_json() for child in self.children]
        return result

    def copy(self):
        return MaketitleNode(self.copy_nodes(self.children))
