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


class AuthorNode(MetadataNode):
    def __init__(self, body: List[ASTNode]):
        super().__init__("author", body)


class AuthorsNode(ASTNode):
    def __init__(self, authors: List[AuthorNode] = []):
        super().__init__()
        self.set_children(authors)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, AuthorsNode):
            return False
        return all(a == b for a, b in zip(self.children, other.children))

    def detokenize(self) -> str:
        """Convert the authors node back to LaTeX source code."""
        return "\n\\and\n".join(author.detokenize() for author in self.children)

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.AUTHOR
        content = []
        for author in self.children:
            author_childs = [child.to_json() for child in author.children]
            content.append(author_childs)
        result["content"] = content
        return result

    def copy(self):
        return AuthorsNode(self.copy_nodes(self.children))
