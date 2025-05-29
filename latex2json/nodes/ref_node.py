from latex2json.nodes.base_nodes import ASTNode
from typing import List


class RefNode(ASTNode):
    def __init__(self, references: str | List[str], title: str = None):
        super().__init__()
        self.references: List[str] = (
            references if isinstance(references, list) else [references]
        )
        self.title = title

    def __str__(self):
        out = f"Ref: {self.references}"
        if self.title:
            out += f", Title: {self.title}"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RefNode):
            return False
        if self.title != other.title:
            return False
        return self.references == other.references

    def detokenize(self):
        return f"\\ref{{{', '.join(self.references)}}}"
