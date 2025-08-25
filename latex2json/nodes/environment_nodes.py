from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.caption_node import CaptionNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.nodes.node_types import NodeTypes


class EnvironmentNode(ASTNode):
    def __init__(
        self,
        env_name: str,
        body: List[ASTNode] = [],
        numbering: Optional[str] = None,
        display_name: Optional[str] = None,
    ):
        super().__init__()
        self.env_name = env_name
        self.numbering = numbering
        self.set_body(body)
        self.display_name = display_name or env_name

    def set_body(self, body: List[ASTNode]):
        self.set_children(strip_whitespace_nodes(body))

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    @property
    def name(self) -> str:
        return self.display_name or self.env_name

    def __str__(self):
        return self.detokenize()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EnvironmentNode):
            return False
        same = self.env_name == other.env_name
        if not same:
            return False
        same = self.display_name == other.display_name
        if not same:
            return False
        return check_asts_equal(self.body, other.body)

    def detokenize(self) -> str:
        """Convert the environment node back to LaTeX source code."""
        # Start with \begin{name}
        out = f"\\begin{{{self.env_name}}}"

        # Add numbering if present
        if self.numbering:
            out += f"[{self.numbering}]"

        # Add body content
        if self.body:
            out += "\n"
            out += "".join(child.detokenize() for child in self.body)
            out += "\n"

        # End with \end{name}
        out += f"\\end{{{self.env_name}}}"

        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.ENVIRONMENT
        result["name"] = self.display_name or self.env_name
        result["content"] = [child.to_json() for child in self.body]
        if self.numbering:
            result["numbering"] = self.numbering
        return result

    def copy(self):
        return EnvironmentNode(
            env_name=self.env_name,
            body=self.copy_nodes(self.body),
            numbering=self.numbering,
            display_name=self.display_name,
        )


class DocumentNode(EnvironmentNode):
    def __init__(self, body: List[ASTNode] = []):
        super().__init__(NodeTypes.DOCUMENT, body)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, DocumentNode):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.DOCUMENT
        del result["name"]
        return result


class TheoremNode(EnvironmentNode):
    def __init__(
        self,
        name: str,
        body: List[ASTNode] = [],
        numbering: Optional[str] = None,
        display_name: Optional[str] = None,
        title: List[ASTNode] = [],
    ):
        super().__init__(name, body, numbering, display_name)
        self.title = title

    def __eq__(self, other: ASTNode):
        if not isinstance(other, TheoremNode):
            return False
        same = super().__eq__(other)
        if not same:
            return False
        return check_asts_equal(self.title, other.title)

    def detokenize(self) -> str:
        """Convert the theorem node back to LaTeX source code."""
        # Start with \begin{name}
        out = f"\\begin{{{self.env_name}}}"

        # Add title if present
        if self.title:
            out += f"[{''.join(child.detokenize() for child in self.title)}]"

        # Add body content
        if self.body:
            out += "\n"
            out += "".join(child.detokenize() for child in self.body)
            out += "\n"

        # End with \end{name}
        out += f"\\end{{{self.env_name}}}"

        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.MATH_ENV  # "theorem"
        if self.title:
            result["title"] = [child.to_json() for child in self.title]
        return result

    def copy(self):
        return TheoremNode(
            name=self.env_name,
            body=self.copy_nodes(self.body),
            numbering=self.numbering,
            display_name=self.display_name,
            title=self.copy_nodes(self.title),
        )


class BaseTableFigureNode(EnvironmentNode):
    def __init__(
        self, env_name: str, body: List[ASTNode] = [], numbering: Optional[str] = None
    ):
        super().__init__(env_name, body, numbering)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, self.__class__):
            return False
        return super().__eq__(other)

    def to_json(self):
        result = super().to_json()
        result["type"] = self.env_name
        if "numbering" not in result:
            # transfer the numbering of caption node to the table/figure itself
            caption_token = None

            # BFS search for type='caption' to extract numbering
            queue = [result["content"]]
            while queue and not caption_token:
                current_level = queue.pop(0)
                for token in current_level:
                    if not isinstance(token, dict):
                        continue
                    if token.get("type") == "caption":
                        caption_token = token
                        break
                    if "content" in token and isinstance(token["content"], list):
                        queue.append(token["content"])
            if caption_token and "numbering" in caption_token:
                result["numbering"] = caption_token["numbering"]
                del caption_token["numbering"]

        return result

    def get_caption_node(self) -> Optional[CaptionNode]:
        for child in self.body:
            if isinstance(child, CaptionNode):
                return child
        return None

    def copy(self):
        return super().copy()


class TableNode(BaseTableFigureNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__(NodeTypes.TABLE, body, numbering)


class SubTableNode(BaseTableFigureNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__(NodeTypes.SUBTABLE, body, numbering)


class FigureNode(BaseTableFigureNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__(NodeTypes.FIGURE, body, numbering)


class SubFigureNode(BaseTableFigureNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__(NodeTypes.SUBFIGURE, body, numbering)


class AlgorithmNode(BaseTableFigureNode):
    def __init__(self, body: List[ASTNode] = [], numbering: Optional[str] = None):
        super().__init__(NodeTypes.ALGORITHM, body, numbering)


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
        result["type"] = NodeTypes.ALGORITHMIC
        result["content"] = self.text
        return result

    def copy(self):
        return AlgorithmicNode(self.text)
