from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from typing import List, Optional

from latex2json.nodes.node_types import NodeTypes


class BaseRefCiteNode(ASTNode):
    __slots__ = ('prefix', 'references', 'title')

    def __init__(
        self, prefix: str, references: str | List[str], title: Optional[List[ASTNode]] = None
    ):
        super().__init__()
        self.prefix = prefix
        self.references: List[str] = (
            references if isinstance(references, list) else [references]
        )
        self.title = title if title is not None else []

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
            result["title"] = [child.to_json() for child in self.title]
        return result

    def copy(self):
        return BaseRefCiteNode(
            self.prefix, self.references, title=self.copy_nodes(self.title)
        )


class RefNode(BaseRefCiteNode):
    __slots__ = ()

    def __init__(self, references: str | List[str], title: Optional[List[ASTNode]] = None):
        super().__init__(NodeTypes.REF, references, title)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RefNode):
            return False
        return super().__eq__(other)


class CiteNode(BaseRefCiteNode):
    __slots__ = ()

    def __init__(self, references: str | List[str], title: Optional[List[ASTNode]] = None):
        super().__init__(NodeTypes.CITATION, references, title)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CiteNode):
            return False
        return super().__eq__(other)


class URLNode(ASTNode):
    __slots__ = ('url', 'title')

    def __init__(self, url: str, title: Optional[List[ASTNode]] = None):
        super().__init__()
        self.url = url
        self.title = title if title is not None else []

    def __eq__(self, other: ASTNode):
        if not isinstance(other, URLNode):
            return False
        return self.url == other.url and self.title == other.title

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        out = f"\\url"
        if self.title:
            out += f"{{{''.join(child.detokenize() for child in self.title)}}}"
        out += f"{{{self.url}}}"
        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.URL
        result["content"] = self.url
        if self.title:
            result["title"] = [child.to_json() for child in self.title]
        return result

    def copy(self):
        return URLNode(self.url, title=self.copy_nodes(self.title))


class FootnoteNode(ASTNode):
    __slots__ = ('title',)

    def __init__(self, body: Optional[List[ASTNode]] = None, title: Optional[str] = None):
        super().__init__()
        self.set_children(body if body is not None else [])
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
