from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from typing import List, Optional

from latex2json.nodes.node_types import NodeTypes


class BaseRefCiteNode(ASTNode):
    def __init__(
        self, prefix: str, references: str | List[str], title: Optional[str] = None
    ):
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
        out = f"\\{self.prefix}"
        if self.title:
            out += f"[{self.title}]"
        out += f"{{{', '.join(self.references)}}}"
        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = self.prefix
        result["content"] = self.references
        if self.title:
            result["title"] = self.title
        return result

    def copy(self):
        return BaseRefCiteNode(self.prefix, self.references, self.title)


class RefNode(BaseRefCiteNode):
    def __init__(self, references: str | List[str], title: Optional[str] = None):
        super().__init__(NodeTypes.REF, references, title)

        self.filename = None

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RefNode):
            return False
        return super().__eq__(other)


class CiteNode(BaseRefCiteNode):
    def __init__(self, references: str | List[str], title: Optional[str] = None):
        super().__init__(NodeTypes.CITATION, references, title)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CiteNode):
            return False
        return super().__eq__(other)


class URLNode(ASTNode):
    def __init__(self, url: str, title: Optional[str] = None):
        super().__init__()
        self.url = url
        self.title = title

    def __eq__(self, other: ASTNode):
        if not isinstance(other, URLNode):
            return False
        return self.url == other.url and self.title == other.title

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        out = f"\\url"
        if self.title:
            out += f"[{self.title}]"
        out += f"{{{self.url}}}"
        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.URL
        result["content"] = self.url
        if self.title:
            result["title"] = self.title
        return result

    def copy(self):
        return URLNode(self.url, self.title)


class FootnoteNode(ASTNode):
    def __init__(self, body: List[ASTNode], title: Optional[str] = None):
        super().__init__()
        self.set_children(body)
        self.title = title

    def __eq__(self, other: ASTNode):
        if not isinstance(other, FootnoteNode):
            return False
        return (
            check_asts_equal(self.children, other.children)
            and self.title == other.title
        )

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        out = f"\\footnote"
        if self.title:
            out += f"[{self.title}]"
        content = "".join(child.detokenize() for child in self.children)
        out += f"{{{content}}}"
        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.FOOTNOTE
        result["content"] = [child.to_json() for child in self.children]
        if self.title:
            result["title"] = self.title
        return result

    def copy(self):
        return FootnoteNode(self.copy_nodes(self.children), self.title)
