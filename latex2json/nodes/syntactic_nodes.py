import math
from typing import List
from latex2json.nodes.base import ASTNode, check_children_equal

# from latex2json.nodes.utils import check_children_equal


def strip_whitespace(nodes: List[ASTNode]):
    if nodes:
        if isinstance(nodes[0], TextNode):
            text = nodes[0].text.lstrip()
            if text:
                nodes[0].text = text
            else:
                nodes.pop(0)
        if isinstance(nodes[-1], TextNode):
            text = nodes[-1].text.rstrip()
            if text:
                nodes[-1].text = text
            else:
                nodes.pop(-1)


class BeginBraceNode(ASTNode):  # e.g. {
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value

    def detokenize(self):
        return self.value

    def __eq__(self, other: ASTNode):
        if not isinstance(other, BeginBraceNode):
            return False
        return self.value == other.value


class EndBraceNode(ASTNode):  # e.g. }
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return self.value

    def detokenize(self):
        return self.value

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EndBraceNode):
            return False
        return self.value == other.value


class EndOfLineNode(ASTNode):
    def __init__(self):
        pass

    def __str__(self):
        return "EOL"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EndOfLineNode):
            return False
        return True

    def detokenize(self):
        return "\n"


class TextNode(ASTNode):
    def __init__(self, text: str):
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


class BraceNode(ASTNode):
    def __init__(self, children: List[ASTNode]):
        self.set_children(children)

    def strip_whitespace(self):
        strip_whitespace(self.children)

    def __str__(self):
        return f"Brace({', '.join(str(child) for child in self.children)})"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, BraceNode):
            return False
        return super().__eq__(other)

    def detokenize(self):
        child_strs = "".join(child.detokenize() for child in self.children)
        return "{" + child_strs + "}"


class BracketNode(ASTNode):
    def __init__(self, children: List[ASTNode]):
        self.set_children(children)

    def strip_whitespace(self):
        strip_whitespace(self.children)

    def __str__(self):
        return f"Bracket({', '.join(str(child) for child in self.children)})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, BracketNode):
            return False
        return super().__eq__(other)

    def detokenize(self):
        child_strs = "".join(child.detokenize() for child in self.children)
        return "[" + child_strs + "]"


class CommandNode(ASTNode):
    def __init__(
        self, name: str, args: List[ASTNode] = [], opt_args: List[ASTNode] = []
    ):
        self.name = name
        self.args = args
        self.opt_args = opt_args

        self.set_children(self.opt_args + self.args)

    def __str__(self):
        out_str = f"{self.name}"
        if self.args or self.opt_args:
            out_str += f"([{self.opt_args}], {self.args})"
        return out_str

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CommandNode):
            return False
        if self.name != other.name:
            return False
        return check_children_equal(self.args, other.args) and check_children_equal(
            self.opt_args, other.opt_args
        )

    def detokenize(self):
        out = self.name
        if self.opt_args:
            out += "".join(child.detokenize() for child in self.opt_args)
        if self.args:
            out += "".join(child.detokenize() for child in self.args)
        return out


class ArgNode(ASTNode):
    def __init__(self, num: int, num_params: int = 1):
        self.num = num
        self.depth = ArgNode.compute_depth(num_params)
        self.value: List[ASTNode] = []  # store of current arg value

    def get_literal(self):
        text = "#" * 2 ** (self.depth)
        return text + str(self.num)

    @staticmethod
    def compute_depth(num_params: int) -> int:
        return int(math.log(num_params, 2)) if num_params > 0 else -1

    def __str__(self):
        out = f"ArgNode({self.get_literal()})"
        if self.value:
            out += f": {self.value}"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, ArgNode):
            return False
        return self.num == other.num and self.depth == other.depth

    def detokenize(self):
        return self.get_literal()
