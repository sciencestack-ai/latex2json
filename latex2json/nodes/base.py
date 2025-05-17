from typing import List, Optional


class ASTNode:
    children: List["ASTNode"] = []
    parent: Optional["ASTNode"] = None

    def __repr__(self):
        return self.__str__()

    def set_children(self, children: List["ASTNode"]):
        self.children = children
        for child in self.children:
            child.parent = self

    def __eq__(self, other: "ASTNode"):
        if not isinstance(other, self.__class__):
            return False
        return check_asts_equal(self.children, other.children)

    def detokenize(self):
        return "".join(child.detokenize() for child in self.children)


def check_asts_equal(ast1: List[ASTNode], ast2: List[ASTNode]):
    if len(ast1) != len(ast2):
        return False
    for node1, node2 in zip(ast1, ast2):
        if node1 != node2:
            return False
    return True
