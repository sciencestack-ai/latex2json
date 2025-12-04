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
    # Rowspan is corrected to 1 because there's no empty cell in subsequent rows
    assert row2.cells[0].rowspan == 1  # Auto-corrected from declared 2
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
        {\makecell{111 \\ 222}} & 333 \tabularnewline
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
        \multirow{2}{*}{\makecell{\cellcolor[rgb]{1,0,0} 111 \\ 222}} & \multicolumn{2}{c|}{{{333}}}
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]
    assert len(tabular.row_nodes) == 1
    row1 = tabular.row_nodes[0]
    assert len(row1.cells) == 2
    cell1 = row1.cells[0]
    # Rowspan corrected to 1 because there's only 1 row in the table
    assert cell1.rowspan == 1 and cell1.colspan == 1  # Auto-corrected from declared 2
    cell_str = parser.convert_nodes_to_str(cell1.body, postprocess=False).strip()
    assert cell_str.replace(" ", "") == "111\n222"

    # inner cellcolor style is preserved!
    assert cell1.styles == ["color=rgb(255,0,0)"]

    # check that {{{333}}} -> 333
    cell2 = row1.cells[1]
    assert cell2.body == [TextNode("333")]
    assert cell2.colspan == 2


def test_proper_cells_with_braces():
    parser = Parser()

    text = r"""
    \begin{tabular}{c}
        { \bf one single \\ cell } & second cell \\ 
        second row, cell 1 & $\textcolor{red}{\mathbf{A}}$
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

        # but also check that the {} inside last equation cell is preserved
        last_cell = tabular.row_nodes[1].cells[1]
        assert len(last_cell.body) == 1 and isinstance(last_cell.body[0], EquationNode)
        equation = last_cell.body[0]
        assert equation.env_name == "equation"
        assert equation.equation_to_str() == r"\textcolor{red}{\mathbf{A}}"

    assert_out_tabular(out)

    # # check that the same tabular structure works inside an equation too

    # eq_tab_text = r"""\begin{equation}%s\end{equation}""" % (text)
    # out = parser.parse(eq_tab_text, postprocess=True)
    # assert len(out) == 1 and isinstance(out[0], EquationNode)
    # equation = out[0]
    # assert len(equation.children) == 1 and isinstance(equation.children[0], TabularNode)
    # assert_out_tabular(equation.children)


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


def test_build_cell_matrix_with_multirow():
    """Test cell matrix building with multirow spanning."""
    parser = Parser()
    text = r"""
    \begin{tabular}{ccc}
        \multirow{2}{*}{A} & B & C \\
        & D & E
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    # The parser creates 3 cells in row 1: empty, D, E
    # This is correct - the LaTeX has an empty cell at position 0
    assert len(tabular.row_nodes[1].cells) == 3

    matrix = tabular.build_cell_matrix()
    assert len(matrix) == 2  # 2 rows
    assert len(matrix[0]) == 3  # 3 columns

    # First cell should span 2 rows
    cell_a = matrix[0][0]
    assert cell_a.body == [TextNode("A")]
    assert cell_a.rowspan == 2

    # Both row 0 and row 1, column 0 should point to same cell
    assert matrix[0][0] is cell_a
    assert matrix[1][0] is cell_a  # Same cell reference - occupied by multirow

    # Other cells should be different
    assert matrix[0][1].body == [TextNode("B")]
    assert matrix[0][2].body == [TextNode("C")]
    # Row 1: The empty cell from "&" gets pushed to col 1, D to col 2
    # E would be at col 3 but matrix is only 3 cols wide
    assert matrix[1][1].body == []  # Empty cell from "&"
    assert matrix[1][2].body == [TextNode("D")]


def test_build_cell_matrix_with_multicolumn():
    """Test cell matrix building with multicolumn spanning."""
    parser = Parser()
    text = r"""
    \begin{tabular}{ccc}
        \multicolumn{2}{c}{AB} & C \\
        D & E & F
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    matrix = tabular.build_cell_matrix()
    assert len(matrix) == 2  # 2 rows
    assert len(matrix[0]) == 3  # 3 columns

    # First cell should span 2 columns
    cell_ab = matrix[0][0]
    assert cell_ab.body == [TextNode("AB")]
    assert cell_ab.colspan == 2

    # Both column 0 and 1 in row 0 should point to same cell
    assert matrix[0][0] is cell_ab
    assert matrix[0][1] is cell_ab  # Same cell reference

    # Other cells
    assert matrix[0][2].body == [TextNode("C")]
    assert matrix[1][0].body == [TextNode("D")]
    assert matrix[1][1].body == [TextNode("E")]
    assert matrix[1][2].body == [TextNode("F")]


def test_build_cell_matrix_complex():
    """Test cell matrix with both multirow and multicolumn."""
    parser = Parser()
    text = r"""
    \begin{tabular}{cccc}
        \multirow{2}{*}{A} & B & C & D \\
        & \multicolumn{2}{c}{EF} & G \\
        H & I & J & K
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    matrix = tabular.build_cell_matrix()
    assert len(matrix) == 3  # 3 rows
    assert len(matrix[0]) == 4  # 4 columns

    # Cell A spans 2 rows
    cell_a = matrix[0][0]
    assert cell_a.body == [TextNode("A")]
    assert matrix[0][0] is cell_a
    assert matrix[1][0] is cell_a

    # Row 1 has empty cell at [1][1], then EF at [1][2-3]
    assert matrix[1][1].body == []  # Empty cell from "&"

    # Cell EF spans 2 columns starting at col 2
    cell_ef = matrix[1][2]
    assert cell_ef.body == [TextNode("EF")]
    assert cell_ef.colspan == 2
    assert matrix[1][2] is cell_ef
    assert matrix[1][3] is cell_ef


def test_correct_rowspans_automatic():
    """Test that rowspans are automatically corrected during parsing."""
    parser = Parser()
    # Declare multirow{4} but only 2 rows exist
    text = r"""
    \begin{tabular}{ccc}
        \multirow{4}{*}{A} & B & C \\
        & D & E
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    # The rowspan should have been automatically corrected to 2
    cell_a = tabular.row_nodes[0].cells[0]
    assert cell_a.body == [TextNode("A")]
    assert cell_a.rowspan == 2  # Corrected from 4 to 2


def test_correct_rowspans_overdeclared():
    """Test correction when multirow doesn't actually span all declared rows."""
    parser = Parser()
    text = r"""
    \begin{tabular}{ccc}
        \multirow{3}{*}{A} & B & C \\
        & D & E \\
        X & Y & Z
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    # The rowspan should have been corrected to 2 (row 3 has X, not empty)
    cell_a = tabular.row_nodes[0].cells[0]
    assert cell_a.rowspan == 2  # Corrected from 3 to 2


def test_correct_rowspans_multiple_cells():
    """Test correction with multiple multirow cells in same table."""
    parser = Parser()
    text = r"""
    \begin{tabular}{cccc}
        \multirow{3}{*}{1} & \multirow{2}{*}{2} & \multirow{2}{*}{3} & 4 \\
        & & 3 & 4 \\
        1 & 2 & 3 & 4
    \end{tabular}
    """.strip()

    out = parser.parse(text, postprocess=True)
    assert len(out) == 1 and isinstance(out[0], TabularNode)
    tabular = out[0]

    # Cell A: declared 3, should be corrected to 2
    cell_a = tabular.row_nodes[0].cells[0]
    assert cell_a.rowspan == 2  # Corrected from 3

    # Cell B: declared 2, should remain 2 (correct)
    cell_b = tabular.row_nodes[0].cells[1]
    assert cell_b.rowspan == 2  # Already correct

    # Cell C: declared 2, should be 1
    cell_c = tabular.row_nodes[0].cells[2]
    assert cell_c.rowspan == 1  # Corrected from 2 to 1
