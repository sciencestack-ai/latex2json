from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.node_types import NodeTypes
from latex2json.nodes.utils import strip_whitespace_nodes


SECTION_LEVELS = {
    "part": 0,
    "chapter": 0,
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
    "paragraph": 4,
    "subparagraph": 5,
}


class SectionNode(EnvironmentNode):
    __slots__ = ('label',)

    def __init__(
        self,
        name: str,
        body: Optional[List[ASTNode]] = None,
        label: Optional[str] = None,
        numbering: Optional[str] = None,
    ):
        super().__init__(name, body, numbering)
        self.label = label

    def __str__(self):
        out = self.name
        if self.numbering:
            out += f"({self.numbering})"
        if self.label:
            out += f"[{self.label}]"
        if self.body:
            out += f"{{{self.body}}}"
        return out

    def detokenize(self) -> str:
        out = "\\" + self.name
        body_str = "".join(child.detokenize() for child in self.body)
        return out + "{" + body_str + "}"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, SectionNode):
            return False
        same = (
            self.name == other.name
            and self.numbering == other.numbering
            and self.label == other.label
        )
        if not same:
            return False
        return check_asts_equal(self.body, other.body)

    def to_json(self):
        result = ASTNode.to_json(self)
        level = SECTION_LEVELS.get(self.name, 1)

        result["type"] = NodeTypes.SECTION
        body = strip_whitespace_nodes(self.body.copy())
        result["title"] = [child.to_json() for child in body]
        result["level"] = level
        # if self.label:
        #     result["label"] = self.label
        if self.numbering:
            result["numbering"] = self.numbering
        return result

    def copy(self):
        return SectionNode(
            name=self.name,
            body=self.copy_nodes(self.body),
            label=self.label,
            numbering=self.numbering,
        )
