from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.utils import strip_whitespace_nodes


class EnvironmentNode(ASTNode):
    def __init__(
        self,
        name: str,
        body: List[ASTNode] = [],
        numbering: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        super().__init__()
        self.name = name
        self.numbering = numbering
        self.set_body(body)
        self.display_name = display_name or name

    def set_body(self, body: List[ASTNode]):
        self.set_children(strip_whitespace_nodes(body))

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def __str__(self):
        return self.detokenize()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EnvironmentNode):
            return False
        same = self.name == other.name
        if not same:
            return False
        same = self.display_name == other.display_name
        if not same:
            return False
        return check_asts_equal(self.body, other.body)

    def detokenize(self) -> str:
        """Convert the environment node back to LaTeX source code."""
        # Start with \begin{name}
        out = f"\\begin{{{self.name}}}"

        # Add numbering if present
        if self.numbering:
            out += f"[{self.numbering}]"

        # Add body content
        if self.body:
            out += "\n"
            out += "".join(child.detokenize() for child in self.body)
            out += "\n"

        # End with \end{name}
        out += f"\\end{{{self.name}}}"

        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = "environment"
        result["name"] = self.name
        result["content"] = [child.to_json() for child in self.body]
        if self.numbering:
            result["numbering"] = self.numbering
        return result


class TableNode(EnvironmentNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__("table", body, numbering)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, TableNode):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = "table"
        return result


class SubTableNode(EnvironmentNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__("subtable", body, numbering)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, SubTableNode):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = "subtable"
        return result


class FigureNode(EnvironmentNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__("figure", body, numbering)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, FigureNode):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = "figure"
        return result


class SubFigureNode(EnvironmentNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__("subfigure", body, numbering)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, SubFigureNode):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = "subfigure"
        return result


class AlgorithmNode(EnvironmentNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__("algorithm", body, numbering)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, AlgorithmNode):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = "algorithm"
        return result


class AlgorithmicNode(ASTNode):
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def __str__(self):
        return self.detokenize()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, AlgorithmicNode):
            return False
        return self.text == other.text

    def detokenize(self):
        return f"\\begin{{algorithmic}}\n{self.text}\\end{{algorithmic}}"

    def to_json(self):
        result = super().to_json()
        result["type"] = "algorithmic"
        result["content"] = self.text
        return result
