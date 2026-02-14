from typing import List, Optional
from latex2json.nodes.base_nodes import ASTNode, TextNode
from latex2json.nodes.node_types import NodeTypes


class ListItemNode(ASTNode):
    __slots__ = ('label',)

    def __init__(self, body: Optional[List[ASTNode]] = None, label: Optional[str] = None):
        super().__init__()
        self.label = label
        self.set_children(body if body is not None else [])

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def set_body(self, body: List[ASTNode]):
        self.set_children(body)

    def is_empty(self) -> bool:
        """Check if this is an empty list item."""
        return len(self.body) == 0

    def __eq__(self, other: ASTNode):
        if not isinstance(other, ListItemNode):
            return False
        if self.label != other.label:
            return False
        return all(a == b for a, b in zip(self.body, other.body))

    def detokenize(self) -> str:
        """Convert the list item node back to LaTeX source code."""
        content = "".join(child.detokenize() for child in self.body)
        out_str = f"\\item"
        if self.label:
            out_str += f"[{self.label}]"
        if content:
            out_str += f" {content}"
        return out_str

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.ITEM
        result["content"] = [child.to_json() for child in self.children]
        if self.label:
            result["title"] = [TextNode(self.label).to_json()]
        return result

    def copy(self):
        return ListItemNode(
            body=self.copy_nodes(self.body),
            label=self.label,
        )


class ListNode(ASTNode):
    __slots__ = ('list_type', 'is_inline', 'list_items')

    def __init__(
        self,
        list_items: Optional[List[ListItemNode]] = None,
        list_type: str = "itemize",
        is_inline: bool = False,
    ):
        super().__init__()
        self.list_type = list_type  # "itemize", "enumerate", etc.
        self.is_inline = is_inline
        self.list_items = []  # Initialize before set_list_items
        self.set_list_items(list_items if list_items is not None else [])

    def set_list_items(self, list_items: List[ListItemNode]):
        self.list_items = list_items
        self.set_children(self.list_items)

    def add_item(self, item: ListItemNode):
        """Add a list item to the list."""
        self.list_items.append(item)
        self.set_children(self.list_items)

    def is_empty(self) -> bool:
        """Check if this is an empty list."""
        return len(self.list_items) == 0

    def __eq__(self, other: ASTNode):
        if not isinstance(other, ListNode):
            return False
        if self.is_inline != other.is_inline:
            return False
        if self.list_type != other.list_type:
            return False
        return all(a == b for a, b in zip(self.list_items, other.list_items))

    def detokenize(self) -> str:
        """Convert the list node back to LaTeX source code."""
        if not self.list_items:
            return f"\\begin{{{self.list_type}}}\\end{{{self.list_type}}}"

        out = f"\\begin{{{self.list_type}}}\n"

        for item in self.list_items:
            out += item.detokenize() + "\n"

        out += f"\\end{{{self.list_type}}}"
        return out

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.LIST
        result["name"] = self.list_type
        result["content"] = [item.to_json() for item in self.list_items]
        if self.is_inline:
            result["inline"] = True
        return result

    def copy(self):
        return ListNode(
            list_items=self.copy_nodes(self.list_items),
            list_type=self.list_type,
            is_inline=self.is_inline,
        )
