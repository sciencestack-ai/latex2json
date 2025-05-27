from typing import List, Optional
from latex2json.nodes.base import ASTNode, check_asts_equal
from latex2json.nodes.environment_nodes import EnvironmentNode


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


def get_section_level(name: str) -> int:
    return SECTION_LEVELS.get(name.lstrip("\\"), 0)


def get_paragraph_level(name: str) -> int:
    return PARAGRAPH_LEVELS.get(name.lstrip("\\"), 0)


class SectionNode(EnvironmentNode):
    def __init__(
        self,
        name: str,
        body: List[ASTNode],
        opt_arg: List[ASTNode] = [],
        numbering: Optional[str] = None,
    ):
        super().__init__(name, body, numbering)
        self.opt_arg = opt_arg

    def __str__(self):
        out = self.name
        if self.numbering:
            out += f"({self.numbering})"
        if self.opt_arg:
            out += f"[{self.opt_arg}]"
        if self.body:
            out += f"{{{self.body}}}"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, SectionNode):
            return False
        same = self.name == other.name and self.numbering == other.numbering
        if not same:
            return False
        return check_asts_equal(self.body, other.body) and check_asts_equal(
            self.opt_arg, other.opt_arg
        )
