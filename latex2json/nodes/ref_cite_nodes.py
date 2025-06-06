from latex2json.nodes.base_nodes import ASTNode
from typing import List


class BaseRefCiteNode(ASTNode):
    def __init__(self, prefix: str, references: str | List[str], title: str = None):
        super().__init__()
        self.prefix = prefix
        self.references: List[str] = (
            references if isinstance(references, list) else [references]
        )
        self.title = title

    def __str__(self):
        return self.detokenize()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, BaseRefCiteNode):
            return False
        if self.title != other.title:
            return False
        return self.references == other.references

    def detokenize(self):
        out = f"{self.prefix}"
        if self.title:
            out += f"[{self.title}]"
        out += f"{{{', '.join(self.references)}}}"
        return out


class RefNode(BaseRefCiteNode):
    def __init__(self, references: str | List[str], title: str = None):
        super().__init__("ref", references, title)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RefNode):
            return False
        return super().__eq__(other)


class CiteNode(BaseRefCiteNode):
    def __init__(self, references: str | List[str], title: str = None):
        super().__init__("cite", references, title)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CiteNode):
            return False
        return super().__eq__(other)
