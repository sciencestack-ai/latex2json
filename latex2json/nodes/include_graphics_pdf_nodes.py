from latex2json.nodes.base_nodes import ASTNode
from typing import Optional


class IncludeGraphicsNode(ASTNode):
    def __init__(self, path: str, page: Optional[int] = None):
        super().__init__()
        self.path = path
        self.page = page

    def __eq__(self, other: ASTNode):
        if not isinstance(other, IncludeGraphicsNode):
            return False
        return self.path == other.path and self.page == other.page

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        out = "\\includegraphics"
        if self.page is not None:
            out += f"[page={self.page}]"
        out += f"{{{self.path}}}"
        return out


class IncludePdfNode(ASTNode):
    def __init__(self, path: str, pages: Optional[str] = None):
        super().__init__()
        self.path = path
        self.pages = pages

    def __eq__(self, other: ASTNode):
        if not isinstance(other, IncludePdfNode):
            return False
        return self.path == other.path and self.pages == other.pages

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        out = "\\includepdf"
        if self.pages is not None:
            is_multi = "," in self.pages or "-" in self.pages
            page_str = "{" + self.pages + "}" if is_multi else self.pages
            out += f"[pages={page_str}]"
        out += f"{{{self.path}}}"
        return out
