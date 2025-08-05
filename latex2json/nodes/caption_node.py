from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.node_types import NodeTypes


class CaptionNode(ASTNode):
    def __init__(
        self,
        body: List[ASTNode],
        opt_arg: List[ASTNode] = [],
        numbering: Optional[str] = None,
    ):
        super().__init__()
        self.opt_arg = opt_arg
        self.numbering = numbering

        self.set_children(body)

    @property
    def body(self) -> List[ASTNode]:
        return self.children

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

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.CAPTION
        result["content"] = [child.to_json() for child in self.body]
        # if self.opt_arg: # TODO?
        #     result["opt_arg"] = [child.to_json() for child in self.opt_arg]
        if self.numbering:
            result["numbering"] = self.numbering
        return result

    def copy(self):
        return CaptionNode(
            body=self.copy_nodes(self.body),
            opt_arg=self.copy_nodes(self.opt_arg),
            numbering=self.numbering,
        )
