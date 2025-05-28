from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.environment_nodes import EnvironmentNode


class CaptionNode(ASTNode):
    def __init__(
        self,
        body: List[ASTNode],
        opt_arg: List[ASTNode] = [],
        numbering: Optional[str] = None,
    ):
        super().__init__()
        self.opt_arg = opt_arg
        self.body = body
        self.opt_arg = opt_arg
        self.numbering = numbering
        self.set_children(self.body + self.opt_arg)

    def __str__(self):
        out = "Caption"
        if self.numbering:
            out += f"({self.numbering})"
        if self.opt_arg:
            out += f"[{self.opt_arg}]"
        if self.body:
            out += f"{{{self.body}}}"
        return out

    def detokenize(self):
        out = "\\caption"
        if self.numbering:
            out += f"({self.numbering})"
        if self.opt_arg:
            out += f"[{''.join(child.detokenize() for child in self.opt_arg)}]"
        if self.body:
            out += f"{{{''.join(child.detokenize() for child in self.body)}}}"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CaptionNode):
            return False
        same = self.numbering == other.numbering
        if not same:
            return False
        return check_asts_equal(self.body, other.body) and check_asts_equal(
            self.opt_arg, other.opt_arg
        )
