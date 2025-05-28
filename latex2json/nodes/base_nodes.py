from typing import List, Optional


class ASTNode:
    def __init__(
        self,
        children: List["ASTNode"] = None,
        parent: Optional["ASTNode"] = None,
        labels: List[str] = None,
        styles: List[str] = None,
    ):
        self.children = children if children is not None else []
        self.parent = parent
        self.labels = labels if labels is not None else []
        self._styles = styles if styles is not None else []

    def __repr__(self):
        return self.__str__()

    def set_children(self, children: List["ASTNode"]):
        if self.children:
            # unparent children
            for child in self.children:
                child.parent = None
        self.children = children
        for child in self.children:
            child.parent = self

    def add_styles(self, styles: List[str], insert_at_front: bool = False):
        if not styles:
            return

        total_styles = self._styles.copy()
        self._styles = []
        if insert_at_front:
            total_styles = styles + total_styles
        else:
            total_styles = total_styles + styles

        for style in total_styles:
            if style not in self._styles:
                self._styles.append(style)

    @property
    def styles(self) -> List[str]:
        return self._styles

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


def flatten(lst: List[List[ASTNode]]) -> List[ASTNode]:
    return [item for sublist in lst for item in sublist]


class TextNode(ASTNode):
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def __str__(self):
        return f"'{self.text}'"

    def is_whitespace(self):
        return self.text.isspace()

    def split(self, delimiter: str) -> List["TextNode"]:
        return [TextNode(t) for t in self.text.split(delimiter)]

    def to_chars(self) -> List["TextNode"]:
        return [TextNode(c) for c in self.text]

    def __eq__(self, other: ASTNode):
        if not isinstance(other, TextNode):
            return False
        return self.text == other.text

    def detokenize(self):
        return self.text


class CommandNode(ASTNode):
    def __init__(
        self,
        name: str,
        args: List[List[ASTNode]] = [],
        opt_args: List[List[ASTNode]] = [],
        has_star: bool = False,
        numbering: Optional[str] = None,
    ):
        super().__init__()
        self.name = name
        self.args = args
        self.opt_args = opt_args
        self.numbering = numbering
        self.has_star = has_star
        self.set_children(flatten(self.opt_args + self.args))

    @property
    def num_opt_args(self):
        return len(self.opt_args)

    @property
    def num_args(self):
        return len(self.args)

    def __str__(self):
        out = self.detokenize()
        if self.numbering:
            out += f" ({self.numbering})"
        return out

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CommandNode):
            return False
        if self.name != other.name:
            return False
        if len(self.args) != len(other.args):
            return False
        for arg1, arg2 in zip(self.args, other.args):
            if not check_asts_equal(arg1, arg2):
                return False
        if len(self.opt_args) != len(other.opt_args):
            return False
        if self.numbering != other.numbering:
            return False
        return True

    def detokenize(self):
        out = self.name
        if not out.startswith("\\"):
            out = "\\" + out
        for opt_arg in self.opt_args:
            out += "[" + "".join(child.detokenize() for child in opt_arg) + "]"
        for arg in self.args:
            out += "{" + "".join(child.detokenize() for child in arg) + "}"
        return out
