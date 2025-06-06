from latex2json.nodes.base_nodes import ASTNode
from typing import List, Optional


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
        out = f"{self.prefix}"
        if self.title:
            out += f"[{self.title}]"
        out += f"{{{', '.join(self.references)}}}"
        return out


class RefNode(BaseRefCiteNode):
    def __init__(self, references: str | List[str], title: Optional[str] = None):
        super().__init__("ref", references, title)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RefNode):
            return False
        return super().__eq__(other)


class CiteNode(BaseRefCiteNode):
    def __init__(self, references: str | List[str], title: Optional[str] = None):
        super().__init__("cite", references, title)

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


class FootnoteNode(ASTNode):
    def __init__(self, text: str, title: Optional[str] = None):
        super().__init__()
        self.text = text
        self.title = title

    def __eq__(self, other: ASTNode):
        if not isinstance(other, FootnoteNode):
            return False
        return self.text == other.text and self.title == other.title

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        out = f"\\footnote"
        if self.title:
            out += f"[{self.title}]"
        out += f"{{{self.text}}}"
        return out
