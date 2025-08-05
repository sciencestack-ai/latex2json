from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.node_types import NodeTypes


SECTION_LEVELS = {
    "part": 0,
    "chapter": 1,
    "section": 1,
    "subsection": 2,
    "subsubsection": 3,
}

PARAGRAPH_LEVELS = {
    "paragraph": 1,
    "subparagraph": 2,
}


class SectionNode(EnvironmentNode):
    def __init__(
        self,
        name: str,
        body: List[ASTNode],
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
        is_paragraph = "paragraph" in self.name
        level = 0
        if is_paragraph:
            level = PARAGRAPH_LEVELS.get(self.name, 1)
        else:
            level = SECTION_LEVELS.get(self.name, 1)

        result["type"] = NodeTypes.PARAGRAPH if is_paragraph else NodeTypes.SECTION
        result["title"] = [child.to_json() for child in self.body]
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
