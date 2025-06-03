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
        self.body = strip_whitespace_nodes(body)
        self.set_children(self.body)

    def __str__(self):
        return self.detokenize()

    def __repr__(self):
        return self.__str__()

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
            out += "\n".join(child.detokenize() for child in self.body)
            out += "\n"

        # End with \end{name}
        out += f"\\end{{{self.name}}}"

        return out
