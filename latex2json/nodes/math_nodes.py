from typing import List, Optional
from latex2json.nodes.base_nodes import (
    ASTNode,
    DisplayType,
    check_asts_equal,
    CommandNode,
    TextNode,
)

from latex2json.nodes.utils import merge_text_nodes, strip_whitespace_nodes


def strip_balanced_braces(text: str) -> str:
    # Strip balanced braces from start/end using stack matching
    while text and text.startswith("{"):
        # Check if braces are balanced and match at start/end
        stack = []
        balanced = True
        should_strip = False

        for i, char in enumerate(text):
            if char == "{":
                stack.append(i)
            elif char == "}":
                if not stack:
                    balanced = False
                    break
                start_pos = stack.pop()
                # If this is the closing brace and matches opening,
                # and there are no other unmatched braces
                if not stack and i == len(text) - 1 and start_pos == 0:
                    should_strip = True

        # Only continue if we found a matching pair to strip
        if not balanced or not should_strip:
            break

        text = text[1:-1]

    return text


class EquationNode(ASTNode):
    def __init__(
        self,
        math_nodes: List[ASTNode],
        env_name: str = "equation",
        equation_type: DisplayType = DisplayType.INLINE,
        numbering: Optional[str] = None,
        args: Optional[List[str]] = None,
    ):
        super().__init__()
        self.numbering = numbering
        self.equation_type = equation_type
        self.env_name = env_name
        self.args = args

        self.set_body(math_nodes)

    def set_body(self, body: List[ASTNode]):
        body = strip_whitespace_nodes(body)
        self.set_children(body)

    def __str__(self):
        return self.detokenize() + (f" ({self.numbering})" if self.numbering else "")

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EquationNode):
            return False
        if self.equation_type != other.equation_type:
            return False
        if self.numbering != other.numbering:
            return False
        if self.env_name != other.env_name:
            return False
        return check_asts_equal(self.children, other.children)

    def equation_to_str(self):
        eq_str = ""
        N = len(self.children)

        prev_node = None
        # if we're converting to a string, we need to be careful about textnodes rightafter commands
        for i, node in enumerate(self.children):
            if isinstance(node, TextNode) and isinstance(prev_node, CommandNode):
                if node.text and node.text[0].isalpha():
                    eq_str += " "
            eq_str += node.detokenize()
            prev_node = node
        return eq_str

    def detokenize(self):
        math_str = self.equation_to_str()
        if self.equation_type == DisplayType.INLINE:
            return "$" + math_str + "$"

        if self.equation_type == DisplayType.BLOCK and not self.numbering:
            return "$$" + math_str + "$$"

        env_name = self.env_name
        begin_str = f"\\begin{{{env_name}}}"
        end_str = f"\\end{{{env_name}}}"
        return begin_str + math_str + end_str

    def to_json(self):
        result = super().to_json()
        result["type"] = "equation"
        result["name"] = self.env_name
        result["display"] = self.equation_type.value
        if self.args:
            result["args"] = self.args
        if self.numbering:
            result["numbering"] = self.numbering

        # convert command nodes to text nodes
        nodes = []
        for child in self.children:
            if isinstance(child, CommandNode):
                # if we're converting to a string, we need to be careful about textnodes rightafter commands
                # so we add a space after the command
                cmd_str = "\\" + child.name
                if cmd_str[-1].isalpha():
                    cmd_str += " "
                nodes.append(TextNode(cmd_str))
            else:
                nodes.append(child.copy())
        nodes = merge_text_nodes(nodes)
        content_json = [node.to_json() for node in nodes]

        # strip outer {...} braces from text
        for token in content_json:
            if token.get("type") == "text":
                token["content"] = strip_balanced_braces(token["content"])
        result["content"] = content_json

        return result
