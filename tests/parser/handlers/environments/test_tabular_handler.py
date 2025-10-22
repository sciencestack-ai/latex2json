from typing import List
import pytest

from latex2json.nodes.base_nodes import ASTNode, TextNode
from latex2json.nodes.math_nodes import EquationNode
from latex2json.nodes.tabular_node import CellNode, RowNode, TabularNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_tabular_with_multirow_col():
    parser = Parser()

    text = r"""
    \begin{tabular}{c|c|c}
        \\ % first row is empty, stripped
        1 & 2abc & & 3 \\ 
        \\ % not stripped, should be a single cell containing space if space itself is not stripped
        \multicolumn{3}{|c|{xxx}}{\multirow{2}{*}{4}} & 6
        \\ % last row is empty, stripped
    \end{tabular}
""".strip()

    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    assert len(tabular.row_nodes) == 3
    assert len(tabular.row_nodes[0].cells) == 4
    assert len(tabular.row_nodes[1].cells) == 1
    assert len(tabular.row_nodes[2].cells) == 2

    row1 = tabular.row_nodes[0]
    row2 = tabular.row_nodes[2]

    # assert tabular.row_nodes[1] == RowNode([CellNode(body=[TextNode("")])])

    assert row1.cells[0].body == [TextNode("1")]
    assert row1.cells[1].body == [TextNode("2abc")]
    assert row1.cells[2].body == []  # preserve empty cells!
    assert row1.cells[3].body == [TextNode("3")]

    assert row2.cells[0].body == [TextNode("4")]
    assert row2.cells[0].rowspan == 2
    assert row2.cells[0].colspan == 3
    assert row2.cells[1].body == [TextNode("6")]


def test_nested_tabular():
    parser = Parser()

    text = r"""
    \def\postinner{POST INNER TABLE}
    \begin{tabular}{c}
        \label{outer:tab1}
        FIRST 
        &
        \begin{tabulary}{c}
            \label{inner:tab1}
            \begin{tabular}{c} 111 \end{tabular} & 22\& \\ 
            33 & 44
        \end{tabulary} \postinner
        & 
        \begin{tabular*}{c} \multicolumn{2}{c|}{222} \end{tabular*} 
        & 
        LAST
    \end{tabular}
    """.strip()

    out = parser.parse(text)
    out = strip_whitespace_nodes(out)

    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    assert tabular.labels == ["outer:tab1"]

    assert len(tabular.row_nodes) == 1

    first_cell = tabular.row_nodes[0].cells[0]
    assert len(first_cell.body) == 1
    assert isinstance(first_cell.body[0], TextNode)
    assert first_cell.body[0].text == "FIRST"

    last_cell = tabular.row_nodes[0].cells[-1]
    assert len(last_cell.body) == 1
    assert isinstance(last_cell.body[0], TextNode)
    assert last_cell.body[0].text == "LAST"

    second_cell = tabular.row_nodes[0].cells[1]
    assert len(second_cell.body) == 2
    assert isinstance(second_cell.body[0], TabularNode)
    assert isinstance(second_cell.body[1], TextNode)
    assert second_cell.body[1].text == " POST INNER TABLE"
    inner_tab1 = second_cell.body[0]
    assert inner_tab1.labels == ["inner:tab1"]
    assert len(inner_tab1.row_nodes) == 2
    inner_tab1_r1 = inner_tab1.row_nodes[0]
    inner_tab1_r2 = inner_tab1.row_nodes[1]
    assert len(inner_tab1_r1.cells) == 2
    assert len(inner_tab1_r2.cells) == 2
    # assert inner_tab1_r1.cells[0].body == [TextNode("111")]
    assert inner_tab1_r1.cells[0].body == [
        TabularNode([RowNode([CellNode(body=[TextNode("111")])])])
    ]
    assert inner_tab1_r1.cells[1].body == parser.parse(r"22\&")
    assert inner_tab1_r2.cells[0].body == [TextNode("33")]
    assert inner_tab1_r2.cells[1].body == [TextNode("44")]

    #
    third_cell = tabular.row_nodes[0].cells[2]
    assert third_cell.body == [
        TabularNode([RowNode([CellNode(body=[TextNode("222")], colspan=2)])])
    ]


def test_with_makecell():
    parser = Parser()

    text = r"""
    \begin{tabular}{c}
        \makecell{111 \\ 222} & 333 \tabularnewline
        444 & \shortstack{555 \\ 666}
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]
    assert len(tabular.row_nodes) == 2
    assert len(tabular.row_nodes[0].cells) == 2
    assert len(tabular.row_nodes[1].cells) == 2

    row1 = tabular.row_nodes[0]
    cell1 = row1.cells[0]
    cell1_str = "".join(node.detokenize() for node in cell1.body)
    assert cell1_str.strip() == "111\n222"

    assert row1.cells[1].body == [TextNode("333")]

    row2 = tabular.row_nodes[1]
    assert row2.cells[0].body == [TextNode("444")]
    last_cell = row2.cells[-1]
    last_cell_str = "".join(node.detokenize() for node in last_cell.body)
    assert last_cell_str.strip() == "555\n666"


def test_cellcolor_and_styling():
    parser = Parser()

    # test cellcolor nested inside makecell inside multirow
    text = r"""
    \begin{tabular}{c}
        \multirow{2}{*}{\makecell{\cellcolor[rgb]{1,0,0} 111 \\ 222}}
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]
    assert len(tabular.row_nodes) == 1
    row1 = tabular.row_nodes[0]
    assert len(row1.cells) == 1
    cell1 = row1.cells[0]
    assert cell1.rowspan == 2 and cell1.colspan == 1
    cell_str = parser.convert_nodes_to_str(cell1.body, postprocess=False).strip()
    assert cell_str.replace(" ", "") == "111\n222"

    # inner cellcolor style is preserved!
    assert cell1.styles == ["color=rgb(255,0,0)"]


def test_proper_cells_with_braces():
    parser = Parser()

    text = r"""
    \begin{tabular}{c}
        { \bf one single \\ cell } & second cell \\ 
        second row, cell 1 & second row, cell 2 
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)

    def assert_out_tabular(out: List[ASTNode]):
        assert len(out) == 1 and isinstance(out[0], TabularNode)
        tabular = out[0]
        assert len(tabular.row_nodes) == 2
        assert len(tabular.row_nodes[0].cells) == 2
        assert len(tabular.row_nodes[1].cells) == 2

        row1_cell1 = tabular.row_nodes[0].cells[0]
        assert len(row1_cell1.body) == 1 and isinstance(row1_cell1.body[0], TextNode)
        cell1_text = row1_cell1.body[0]
        assert cell1_text.styles == ["bold"]
        # { \bf one single \\ cell } -> one single\ncell
        assert cell1_text.text.replace(" ", "") == "onesingle\ncell"

    assert_out_tabular(out)

    # check that the same tabular structure works inside an equation too

    eq_tab_text = r"""\begin{equation}%s\end{equation}""" % (text)
    out = parser.parse(eq_tab_text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    equation = out[0]
    assert len(equation.children) == 1 and isinstance(equation.children[0], TabularNode)
    assert_out_tabular(equation.children)


def test_nicetabular():
    parser = Parser()

    text = r"""
    \begin{NiceTabular}{l}[...]
    \label{tab:example}
    \CodeBefore
    \Body
    \CodeAfter

    Last name & First name & Birth day
    \end{NiceTabular}
    """.strip()
    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]
    assert tabular.labels == ["tab:example"]
    assert len(tabular.row_nodes) == 1
    row0_cells = tabular.row_nodes[0].cells
    assert len(row0_cells) == 3
    assert row0_cells[0].body == [TextNode("Last name")]
    assert row0_cells[1].body == [TextNode("First name")]
    assert row0_cells[2].body == [TextNode("Birth day")]
