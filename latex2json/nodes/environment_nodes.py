from typing import List, Optional
from latex2json.nodes.base import ASTNode, check_asts_equal
from latex2json.nodes.syntactic_nodes import strip_whitespace_nodes


class EnvironmentNode(ASTNode):
    def __init__(
        self,
        name: str,
        body: List[ASTNode] = [],
        numbering: Optional[str] = None,
    ):
        self.name = name
        self.numbering = numbering
        self.set_body(body)

        # strip_whitespace(self.body)

        # self.set_children(self.body)

    def set_body(self, body: List[ASTNode]):
        self.body = strip_whitespace_nodes(body)

    def __str__(self):
        out = f"Environment: {self.name}"
        if self.numbering:
            out += f" ({self.numbering})"
        out += "\n"
        out += "\n".join(str(child) for child in self.body)
        out += f"\nEND Environment: {self.name}"
        if self.numbering:
            out += f" ({self.numbering})"
        out += "\n"
        return out

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EnvironmentNode):
            return False
        same = self.name == other.name
        if not same:
            return False
        return check_asts_equal(self.body, other.body)
