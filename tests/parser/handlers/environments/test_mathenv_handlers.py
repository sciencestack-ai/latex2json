import pytest
from latex2json.nodes import (
    TextNode,
    EquationArrayNode,
    EquationNode,
    RowNode,
    CellNode,
    RefNode,
)


from latex2json.parser.parser import Parser


def test_ensuremath_handler():
    parser = Parser()

    text = r"\ensuremath{x^2}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    assert out == [EquationNode([TextNode("x^2")])]


def test_math_env_handlers():
    parser = Parser()

    text = r"""
    \begin{align} 
    a & b \label{eq:1} \\
    \nonumber 
    \begin{matrix} 
    a & b \\
        c & d
    \end{matrix} 
    \\ 
    \begin{array}{2} 
    a & b 
    \end{array} 44 \ref{eq:1} & 55 
    \end{align}
    """.strip()
    out = parser.parse(text)
    assert (
        len(out) == 1
        and isinstance(out[0], EquationArrayNode)
        and out[0].env_name == "align"
    )

    childs = out[0].children
    align_node_json = out[0].to_json()
    childs_json = align_node_json["rows"]

    # check childs labels + numbering
    assert len(childs) == 3
    assert isinstance(childs[0], RowNode)
    assert isinstance(childs[1], RowNode)
    assert isinstance(childs[2], RowNode)
    assert childs[0].labels == ["eq:1"]
    assert childs_json[0].get("numbering") == "1"
    assert childs_json[0].get("labels") == ["eq:1"]
    assert childs_json[1].get("numbering") is None  # \nonumber
    assert childs_json[2].get("numbering") == "2"

    assert childs[0].cells == [CellNode([TextNode("a")]), CellNode([TextNode("b")])]
    matrix_node = EquationArrayNode(
        env_name="matrix",
        row_nodes=[
            RowNode(cells=[CellNode([TextNode("a")]), CellNode([TextNode("b")])]),
            RowNode(cells=[CellNode([TextNode("c")]), CellNode([TextNode("d")])]),
        ],
    )
    assert childs[1].cells == [CellNode([matrix_node])]

    array_node = EquationArrayNode(
        env_name="array",
        row_nodes=[
            RowNode(cells=[CellNode([TextNode("a")]), CellNode([TextNode("b")])]),
        ],
    )
    assert childs[2].cells == [
        CellNode([array_node, TextNode(" 44 "), RefNode(["eq:1"])]),
        CellNode([TextNode("55")]),
    ]
