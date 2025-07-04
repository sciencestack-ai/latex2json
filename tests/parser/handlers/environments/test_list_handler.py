import pytest

from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.list_item_node import ListItemNode, ListNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_list_with_custom_labels():
    parser = Parser()

    text = r"""
    \begin{itemize}
        \item[•] Custom bullet
        \item[1.] Custom number
        \item[\star] Custom symbol
        \item Regular item
    \end{itemize}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    list_node = out[0]

    assert len(list_node.list_items) == 4

    # First item with custom bullet
    assert list_node.list_items[0].label == "•"
    assert list_node.list_items[0].body == [TextNode("Custom bullet")]

    # Second item with custom number
    assert list_node.list_items[1].label == "1."
    assert list_node.list_items[1].body == [TextNode("Custom number")]

    # Third item with LaTeX symbol
    assert list_node.list_items[2].label == "⋆"
    assert list_node.list_items[2].body == [TextNode("Custom symbol")]

    # Fourth item without custom label
    assert list_node.list_items[3].label is None
    assert list_node.list_items[3].body == [TextNode("Regular item")]


def test_nested_lists():
    parser = Parser()

    text = r"""
    \begin{itemize}
        \label{list:item1}
        \item First level item
        \begin{enumerate}
            \item[a)] Nested numbered item
            \item Another nested item
        \end{enumerate}
        \item Back to first level
        \item Third item with nested list
        \begin{itemize}
            \item Nested bullet
            \item Another nested bullet
        \end{itemize}
    \end{itemize}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    outer_list = out[0]

    assert outer_list.labels == ["list:item1"]

    assert outer_list.list_type == "itemize"
    assert len(outer_list.list_items) == 3

    # First item should contain text and a nested enumerate
    first_item = outer_list.list_items[0]
    assert len(first_item.body) == 2
    assert isinstance(first_item.body[0], TextNode)
    assert first_item.body[0].text.strip() == "First level item"
    assert isinstance(first_item.body[1], ListNode)

    nested_enum = first_item.body[1]
    assert nested_enum.list_type == "enumerate"
    assert len(nested_enum.list_items) == 2
    assert nested_enum.list_items[0].label == "a)"
    assert nested_enum.list_items[0].body == [TextNode("Nested numbered item")]
    assert nested_enum.list_items[1].body == [TextNode("Another nested item")]

    # Second item should be simple
    assert outer_list.list_items[1].body == [TextNode("Back to first level")]

    # Third item should contain text and nested itemize
    third_item = outer_list.list_items[2]
    assert len(third_item.body) == 2
    assert isinstance(third_item.body[0], TextNode)
    assert third_item.body[0].text.strip() == "Third item with nested list"
    assert isinstance(third_item.body[1], ListNode)

    nested_itemize = third_item.body[1]
    assert nested_itemize.list_type == "itemize"
    assert len(nested_itemize.list_items) == 2


def test_inline_lists():
    parser = Parser()

    text = r"""
    \begin{itemize*}
        \item Inline item 1
        \item Inline item 2
    \end{itemize*}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    list_node = out[0]

    assert list_node.list_type == "itemize"
    assert list_node.is_inline == True
    assert len(list_node.list_items) == 2


def test_description_list():
    parser = Parser()

    text = r"""
    \begin{description}
        \item[Term 1] Description of term 1
        \item[Term 2] Description of term 2
    \end{description}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    list_node = out[0]

    assert list_node.list_type == "description"
    assert len(list_node.list_items) == 2

    assert list_node.list_items[0].label == "Term 1"
    assert list_node.list_items[0].body == [TextNode("Description of term 1")]

    assert list_node.list_items[1].label == "Term 2"
    assert list_node.list_items[1].body == [TextNode("Description of term 2")]


def test_empty_list():
    parser = Parser()

    text = r"""
    \begin{itemize}
    \end{itemize}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    list_node = out[0]

    assert list_node.list_type == "itemize"
    assert len(list_node.list_items) == 0
    assert list_node.is_empty()


def test_list_with_complex_content():
    parser = Parser()

    text = r"""
    \begin{itemize}
        \item Item with \textbf{bold} text and \emph{emphasis}
        \item Item with math: $x^2 + y^2 = z^2$
        \item Item with command: \LaTeX\ is great
    \end{itemize}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    list_node = out[0]

    assert len(list_node.list_items) == 3

    # First item should contain text and command nodes
    first_item = list_node.list_items[0]
    assert len(first_item.body) > 1
    # Should contain TextNode, CommandNode for \textbf, TextNode, CommandNode for \emph, etc.

    # Second item should contain math
    second_item = list_node.list_items[1]
    assert len(second_item.body) > 1

    # Third item should contain LaTeX command
    third_item = list_node.list_items[2]
    assert len(third_item.body) > 1


def test_list_detokenize():
    parser = Parser()

    text = r"""
    \begin{itemize}
        \item[•] First item
        \item Second item
    \end{itemize}
    """.strip()

    out = parser.parse(text)
    list_node = out[0]

    detokenized = list_node.detokenize()

    # Should contain the basic structure
    assert "\\begin{itemize}" in detokenized
    assert "\\end{itemize}" in detokenized
    assert "\\item[•] First item" in detokenized
    assert "\\item Second item" in detokenized


def test_list_equality():
    parser = Parser()

    text1 = r"""
    \begin{itemize}
        \item First
        \item Second
    \end{itemize}
    """.strip()

    text2 = r"""
    \begin{itemize}
        \item First
        \item Second
    \end{itemize}
    """.strip()

    text3 = r"""
    \begin{enumerate}
        \item First
        \item Second
    \end{enumerate}
    """.strip()

    out1 = parser.parse(text1)
    out2 = parser.parse(text2)
    out3 = parser.parse(text3)

    # Same content should be equal
    assert out1[0] == out2[0]

    # Different list types should not be equal
    assert out1[0] != out3[0]


def test_list_item_equality():
    item1 = ListItemNode([TextNode("test")], "label")
    item2 = ListItemNode([TextNode("test")], "label")
    item3 = ListItemNode([TextNode("different")], "label")
    item4 = ListItemNode([TextNode("test")], "different")

    assert item1 == item2
    assert item1 != item3
    assert item1 != item4


def test_multiline_items():
    parser = Parser()

    text = r"""
    \begin{itemize}
        \item This is a long item
              that spans multiple lines
              in the source
        \item Another item
    \end{itemize}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], ListNode)
    list_node = out[0]

    assert len(list_node.list_items) == 2

    # First item should contain all the text (whitespace handling may vary)
    first_item_text = "".join(
        node.detokenize()
        for node in list_node.list_items[0].body
        if isinstance(node, TextNode)
    )
    assert first_item_text.startswith("This is a long item")
    assert "that spans multiple lines" in first_item_text
    assert first_item_text.endswith("in the source")
