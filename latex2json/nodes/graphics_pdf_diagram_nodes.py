from latex2json.nodes.base_nodes import ASTNode
from typing import Optional
from latex2json.nodes.node_types import NodeTypes


class IncludeGraphicsNode(ASTNode):
    def __init__(
        self, path: str, page: Optional[int] = None, code: Optional[str] = None
    ):
        super().__init__()
        self.path = path
        self.page = page
        # code is metadata for verbatim blocks like \begin{overpic}...
        self.code = code

    def __eq__(self, other: ASTNode):
        if not isinstance(other, IncludeGraphicsNode):
            return False
        return (
            self.path == other.path
            and self.page == other.page
            and self.code == other.code
        )

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        if self.code:
            return self.code

        out = "\\includegraphics"
        if self.page is not None:
            out += f"[page={self.page}]"
        out += f"{{{self.path}}}"
        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.INCLUDEGRAPHICS
        result["content"] = self.path
        if self.page is not None:
            result["page"] = self.page
        if self.code is not None:
            result["code"] = self.code
        return result

    def copy(self):
        return IncludeGraphicsNode(self.path, page=self.page, code=self.code)


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

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.INCLUDEPDF
        result["content"] = self.path
        if self.pages is not None:
            result["pages"] = self.pages
        return result

    def copy(self):
        return IncludePdfNode(self.path, self.pages)


class DiagramNode(ASTNode):
    def __init__(self, env_name: str, diagram: str):
        super().__init__()
        self.env_name = env_name
        self.diagram = diagram

    def __eq__(self, other: ASTNode):
        if not isinstance(other, DiagramNode):
            return False
        return self.diagram == other.diagram and self.env_name == other.env_name

    def __str__(self):
        return self.detokenize()

    def detokenize(self):
        return self.diagram

    def to_json(self):
        result = {}
        result["type"] = NodeTypes.DIAGRAM
        result["name"] = self.env_name
        result["content"] = self.diagram
        return result

    def copy(self):
        return DiagramNode(self.env_name, self.diagram)
