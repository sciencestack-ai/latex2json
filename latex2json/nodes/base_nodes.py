from copy import deepcopy
from enum import Enum
from typing import List, Optional


class DisplayType(Enum):
    INLINE = "inline"
    BLOCK = "block"


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

        self.children = children.copy()
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

        # check parent styles to prevent child dupes
        parent_styles = self.parent.styles if self.parent else []

        for style in total_styles:
            if style not in self._styles and style not in parent_styles:
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

    def to_json(self):
        """Base to_json implementation that handles styles and labels.
        Child classes should call this using super().to_json() and extend it with their own fields.
        """
        result = {}

        if self.styles:
            result["styles"] = self.styles.copy()

        if self.labels:
            result["labels"] = self.labels.copy()

        return result

    def copy(self):
        return deepcopy(self)


def check_asts_equal(ast1: List[ASTNode], ast2: List[ASTNode]):
    if len(ast1) != len(ast2):
        return False
    for node1, node2 in zip(ast1, ast2):
        if node1 != node2:
            return False
    return True


class TextNode(ASTNode):
    def __init__(self, text: str):
        super().__init__()
        self.text = text

    def __str__(self):
        return f"'{self.text}'"

    def is_whitespace(self):
        return self.text == "" or self.text.isspace()

    def split(self, delimiter: str) -> List["TextNode"]:
        return [TextNode(t) for t in self.text.split(delimiter)]

    def __eq__(self, other: ASTNode):
        if not isinstance(other, TextNode):
            return False
        return self.text == other.text

    def detokenize(self):
        return self.text

    def to_json(self):
        result = super().to_json()
        result["type"] = "text"
        result["content"] = self.text
        return result


class AlignmentNode(ASTNode):
    def __init__(self, value: str):
        super().__init__()
        self.value = value  # Usually "&"

    def __str__(self):
        return f"AlignmentNode({self.value})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, AlignmentNode):
            return False
        return self.value == other.value

    def detokenize(self):
        return self.value

    def to_json(self):
        # this node should not ever be needed to be json, but just in case
        result = super().to_json()
        result["type"] = "text"
        result["content"] = self.value
        return result


class GroupNode(ASTNode):
    def __init__(self, body: List[ASTNode]):
        super().__init__()
        self.body = body
        self.set_children(body)

    def set_body(self, body: List[ASTNode]):
        self.set_children(body)

    def __str__(self):
        return f"GroupNode({self.body})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, GroupNode):
            return False
        return check_asts_equal(self.body, other.body)

    def detokenize(self):
        return "{\n" + "".join(child.detokenize() for child in self.body) + "\n}"

    def to_json(self):
        result = super().to_json()
        result["type"] = "group"
        result["content"] = [child.to_json() for child in self.children]
        return result


class VerbatimNode(ASTNode):
    def __init__(
        self,
        text: str,
        title: Optional[str] = None,
        display: Optional[DisplayType] = None,
    ):
        super().__init__()
        self.text = text
        self.title = title
        self.display = display

    def __str__(self):
        out = "VerbatimNode("
        if self.title:
            out += f"title={self.title}, "
        out += f"text={self.text})"
        return out

    def __eq__(self, other: ASTNode):
        if not isinstance(other, VerbatimNode):
            return False
        return (
            self.text == other.text
            and self.display == other.display
            and self.title == other.title
        )

    def detokenize(self):
        return self.text  # not exactly accurate, but good enough for now

    def to_json(self):
        result = super().to_json()
        result["type"] = "code"
        result["content"] = self.text
        result["display"] = self.display.value if self.display else None
        if self.title:
            result["title"] = self.title
        return result


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
        self.numbering = numbering
        self.has_star = has_star
        # Store structure metadata

        self.args = args
        self.opt_args = opt_args

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
        if not check_asts_equal(self.children, other.children):
            return False
        if self.numbering != other.numbering:
            return False
        return True

    def detokenize(self):
        out = "\\" + self.name
        for arg in self.opt_args:
            out += "[" + "".join(child.detokenize() for child in arg) + "]"
        for arg in self.args:
            out += "{" + "".join(child.detokenize() for child in arg) + "}"
        return out

    def to_json(self):
        result = super().to_json()
        result["type"] = "command"
        result["command"] = self.name
        if self.args:
            result["args"] = [[child.to_json() for child in arg] for arg in self.args]
        if self.opt_args:
            result["opt_args"] = [
                [child.to_json() for child in arg] for arg in self.opt_args
            ]
        return result
