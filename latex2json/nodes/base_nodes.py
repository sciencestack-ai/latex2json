from abc import ABC, abstractmethod
from enum import Enum
from typing import List, Optional

from latex2json.nodes.node_types import NodeTypes


class DisplayType(Enum):
    INLINE = "inline"
    BLOCK = "block"


class ASTNode(ABC):
    __slots__ = ('_children', 'parent', '_labels', '_styles',
                 'should_postprocess', 'is_math', 'source_file')

    def __init__(
        self,
        children: List["ASTNode"] = None,
        parent: Optional["ASTNode"] = None,
        labels: List[str] = None,
        styles: List[str] = None,
    ):
        self._children = children  # None means no children (lazy init)
        self.parent = parent
        self._labels = labels  # None means no labels (lazy init)
        self._styles = styles  # None means no styles (lazy init)

        # variables for postprocessing
        self.should_postprocess = True
        self.is_math = False
        self.source_file: Optional[str] = None

    @property
    def children(self) -> List["ASTNode"]:
        if self._children is None:
            self._children = []
        return self._children

    @children.setter
    def children(self, value: List["ASTNode"]):
        self._children = value if value else None

    @property
    def labels(self) -> List[str]:
        if self._labels is None:
            self._labels = []
        return self._labels

    @labels.setter
    def labels(self, value: List[str]):
        self._labels = value if value else None

    def __repr__(self):
        return self.__str__()

    def get_source_file(self) -> Optional[str]:
        if self.source_file:
            return self.source_file
        if self.parent:
            return self.parent.get_source_file()
        return None

    def set_children(self, children: List["ASTNode"]):
        if self._children:
            # unparent children
            for child in self._children:
                child.parent = None

        self._children = children if children else None
        for child in children:
            child.parent = self

    def add_styles(self, styles: List[str], insert_at_front: bool = False):
        if not styles:
            return

        if insert_at_front:
            total_styles = styles + self.styles
        else:
            total_styles = self.styles + styles

        # check parent styles to prevent child dupes
        parent_styles = self.parent.styles if self.parent else []

        new_styles = []
        for style in total_styles:
            if style not in new_styles and style not in parent_styles:
                new_styles.append(style)
        self._styles = new_styles if new_styles else None

    @property
    def styles(self) -> List[str]:
        if self._styles is None:
            self._styles = []
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

        if self._styles:
            result["styles"] = list(self._styles)

        if self._labels:
            result["labels"] = list(self._labels)

        return result

    @abstractmethod
    def copy(self) -> "ASTNode":
        pass

    @staticmethod
    def copy_nodes(nodes: List["ASTNode"]) -> List["ASTNode"]:
        return [node.copy() for node in nodes]


def check_asts_equal(ast1: List[ASTNode], ast2: List[ASTNode]):
    if len(ast1) != len(ast2):
        return False
    for node1, node2 in zip(ast1, ast2):
        if node1 != node2:
            return False
    return True


class TextNode(ASTNode):
    __slots__ = ('text',)

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
        result["type"] = NodeTypes.TEXT
        result["content"] = self.text
        return result

    def copy(self):
        return TextNode(self.text)


class SpecialCharNode(ASTNode):
    __slots__ = ('value',)

    def __init__(self, value: str):
        super().__init__()
        self.value = value

    def __str__(self):
        return f"SpecialCharNode({self.value})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, SpecialCharNode):
            return False
        return self.value == other.value

    def detokenize(self):
        return self.value

    def to_json(self):
        # this node should not ever be needed to be json, but just in case
        result = super().to_json()
        result["type"] = NodeTypes.TEXT
        result["content"] = self.value
        return result

    def copy(self):
        return SpecialCharNode(self.value)


class AlignmentNode(SpecialCharNode):
    __slots__ = ()  # No additional attributes

    def __init__(self, value: str):
        super().__init__(value)


class GroupNode(ASTNode):
    __slots__ = ()  # Uses _children from parent

    def __init__(self, body: List[ASTNode]):
        super().__init__()
        self.set_body(body)

    def set_body(self, body: List[ASTNode]):
        self.set_children(body)

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def __str__(self):
        return f"GroupNode({self.children})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, GroupNode):
            return False
        return check_asts_equal(self.children, other.children)

    def detokenize(self):
        return "{\n" + "".join(child.detokenize() for child in self.children) + "\n}"

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.GROUP
        result["content"] = [child.to_json() for child in self.children]
        return result

    def copy(self):
        return GroupNode(self.copy_nodes(self.children))


class VerbatimNode(ASTNode):
    __slots__ = ('text', 'title', 'display')

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
        result["type"] = NodeTypes.CODE
        result["content"] = self.text
        result["display"] = self.display.value if self.display else None
        if self.title:
            result["title"] = self.title
        return result

    def copy(self):
        return VerbatimNode(text=self.text, title=self.title, display=self.display)


class CommandNode(ASTNode):
    __slots__ = ('name', 'numbering', 'has_star', 'args', 'opt_args')

    def __init__(
        self,
        name: str,
        args: Optional[List[List[ASTNode]]] = None,
        opt_args: Optional[List[List[ASTNode]]] = None,
        has_star: bool = False,
        numbering: Optional[str] = None,
    ):
        super().__init__()
        self.name = name
        self.numbering = numbering
        self.has_star = has_star
        # Store structure metadata
        self.args = args if args is not None else []
        self.opt_args = opt_args if opt_args is not None else []

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
        result["type"] = NodeTypes.COMMAND
        result["command"] = self.name
        if self.args:
            result["args"] = [[child.to_json() for child in arg] for arg in self.args]
        if self.opt_args:
            result["opt_args"] = [
                [child.to_json() for child in arg] for arg in self.opt_args
            ]
        return result

    def copy(self):
        return CommandNode(
            self.name,
            args=[self.copy_nodes(c) for c in self.args],
            opt_args=[self.copy_nodes(c) for c in self.opt_args],
            has_star=self.has_star,
            numbering=self.numbering,
        )
