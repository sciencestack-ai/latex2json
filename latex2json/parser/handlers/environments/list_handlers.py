from typing import List
from latex2json.nodes.base_nodes import ASTNode, CommandNode
from latex2json.nodes.list_item_node import ListItemNode, ListNode
from latex2json.nodes.utils import split_nodes_by_predicate, strip_whitespace_nodes
from latex2json.parser.parser_core import ParserCore
from latex2json.tokens.types import EnvironmentStartToken, Token


def list_item_handler(parser: ParserCore, token: Token) -> List[ASTNode]:
    parser.skip_whitespace()
    label = parser.parse_bracket_as_nodes() or []
    # return as empty list item node for now. Append body buffer in split_into_items.
    return [ListItemNode([], label=label)]


def split_into_items(nodes: List[ASTNode]) -> List[ListItemNode]:
    """Split into items and append as buffer if non ListItemNode.
    Buffer is then added to the last item."""
    out_items: List[ListItemNode] = []

    buffer: List[ASTNode] = []
    for node in nodes:
        if isinstance(node, ListItemNode):
            if out_items:
                out_items[-1].set_body(strip_whitespace_nodes(buffer))
                buffer = []
            out_items.append(node)
        else:
            buffer.append(node)

    if buffer and out_items:
        out_items[-1].set_body(strip_whitespace_nodes(buffer))
        buffer = []

    return out_items


def list_handler(parser: ParserCore, token: EnvironmentStartToken) -> List[ASTNode]:
    is_inline = token.name.endswith("*")
    list_type = token.name.strip("*")

    # parse as generic environment first
    out = parser.parse_environment(token)
    if not out:
        return []

    env_nodes: List[ASTNode] = out.body
    items = split_into_items(env_nodes)

    list_node = ListNode(items, list_type=list_type, is_inline=is_inline)
    # re-assign labels from environment node
    list_node.labels = out.labels

    return [list_node]


LIST_ENV_NAMES = ["itemize", "enumerate", "description"]
LIST_ENV_NAMES.extend(name + "*" for name in LIST_ENV_NAMES[:])


def register_list_handlers(parser: ParserCore):
    parser.register_handler("item", list_item_handler)

    for env_name in LIST_ENV_NAMES:
        parser.register_env_handler(env_name, list_handler)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    text = r"""
    \begin{itemize}
    \label{list:item1}
    \item Item 1 \begin{itemize}
                \item[3] Item 1.1
                \item Item 1.2
                \end{itemize}
    Post item 1
    \item[basd] Item 2
    \item Item 3
    """.strip()

    parser = Parser()
    out = parser.parse(text)
    print(out)
