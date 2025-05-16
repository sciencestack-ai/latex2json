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
        return check_children_equal(self.children, other.children)

    def detokenize(self):
        return "".join(child.detokenize() for child in self.children)


def check_children_equal(children: List[ASTNode], other_children: List[ASTNode]):
    if len(children) != len(other_children):
        return False
    for child, other_child in zip(children, other_children):
        if child != other_child:
            return False
    return True
