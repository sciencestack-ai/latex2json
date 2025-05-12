from typing import Any, List

from latex2json.nodes.base import ASTNode, check_children_equal
from latex2json.nodes.syntactic_nodes import ArgNode, BraceNode, CommandNode, TextNode
from latex2json.nodes.utils import flatten

# from latex2json.nodes.csname import CSNameNode


class BaseDefinitionNode(ASTNode):
    signatures: List[str] = []
    is_global = False

    def __init__(self, name: str):
        self.name = name


# NEW COMMAND/ENV
class NewCommandNode(BaseDefinitionNode):
    signatures = ["\\newcommand", "\\renewcommand"]
    is_global = True

    def __init__(
        self,
        name: str,
        num_args: int,
        defaults: List[List[ASTNode]],
        definition: List[ASTNode],
        depth=0,
    ):
        super().__init__(name)
        self.num_args = num_args
        self.defaults = defaults
        self.depth = depth
        self.set_children(flatten(defaults) + definition)

    @property
    def definition(self):
        return self.children

    def __str__(self):
        out_str = f"NewCommand:{self.name} [{self.num_args}]"
        if self.defaults:
            out_str += f"({self.defaults})"
        out_str += f"\n{self.definition}"
        return out_str

    def __eq__(self, other: ASTNode):
        if not isinstance(other, NewCommandNode):
            return False
        return (
            self.num_args == other.num_args
            and self.depth == other.depth
            and check_children_equal(self.defaults, other.defaults)
            and check_children_equal(self.definition, other.definition)
        )


class NewEnvironmentNode(BaseDefinitionNode):
    signatures = ["\\newenvironment", "\\renewenvironment"]
    is_global = True

    def __init__(
        self,
        name: str,
        num_args: int,
        before_block: BraceNode,
        after_block: BraceNode,
        defaults: List[List[ASTNode]],
        depth: int = 0,
    ):
        super().__init__(name)
        self.num_args = num_args
        self.before_block = before_block
        self.after_block = after_block
        self.defaults = defaults
        self.depth = depth

        self.set_children(flatten(defaults) + [before_block, after_block])

    def __str__(self):
        out_str = f"NewEnvironment:{self.name} [{self.num_args}]"
        if self.defaults:
            out_str += f"({self.defaults})"
        out_str += f"\nBEFORE:{self.before_block}"
        out_str += f"\nAFTER:{self.after_block}"
        return out_str

    def __eq__(self, other: ASTNode):
        if not isinstance(other, NewEnvironmentNode):
            return False
        return (
            self.name == other.name
            and self.num_args == other.num_args
            and self.depth == other.depth
            and self.before_block == other.before_block
            and self.after_block == other.after_block
            and check_children_equal(self.defaults, other.defaults)
        )


class DefNode(BaseDefinitionNode):
    signatures = ["\\def", "\\gdef", "\\xdef", "\\edef"]

    def __init__(
        self,
        name: str,
        usage_pattern: List[ASTNode],
        definition: List[ASTNode],
        is_lazy: bool = True,  # def/gdef is lazy, edef/xdef is not (expand immediately)
        is_global: bool = False,  # def/edef is local, gdef/xdef is global
    ):
        super().__init__(name)
        self.usage_pattern = usage_pattern
        self.is_lazy = is_lazy
        self.is_global = is_global
        self.set_children(definition)

    def has_csname(self):
        return self.name.startswith(r"\csname")

    @property
    def definition(self):
        return self.children

    @property
    def depth(self):
        depth = -1
        for ele in self.usage_pattern:
            if isinstance(ele, ArgNode):
                return ele.depth
        return depth

    @property
    def num_args(self):
        return len([ele for ele in self.usage_pattern if isinstance(ele, ArgNode)])

    def __str__(self):
        prefix = r"\def"
        if self.is_lazy and self.is_global:
            prefix = r"\gdef"
        elif self.is_global:
            prefix = r"\xdef"
        elif not self.is_lazy:
            prefix = r"\edef"

        out_str = f"{prefix}:{self.name} [{self.num_args}]"
        if self.usage_pattern:
            out_str += f"({self.usage_pattern})"
        out_str += f"\n{self.definition}"
        return out_str

    def __eq__(self, other: ASTNode):
        if not isinstance(other, DefNode):
            return False
        return (
            self.name == other.name
            and self.is_lazy == other.is_lazy
            and self.is_global == other.is_global
            and check_children_equal(self.usage_pattern, other.usage_pattern)
            and check_children_equal(self.definition, other.definition)
        )


class LetNode(BaseDefinitionNode):
    signatures = ["\\let", "\\futurelet"]

    def __init__(
        self, name: str, definition: CommandNode | TextNode, is_future: bool = False
    ):
        super().__init__(name)
        self.definition = definition
        self.is_future = is_future
        self.set_children([definition])

    def __str__(self):
        return f"\\let{self.name}={self.definition}"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, LetNode):
            return False
        return (
            self.name == other.name
            and self.is_future == other.is_future
            and self.definition == other.definition
        )
