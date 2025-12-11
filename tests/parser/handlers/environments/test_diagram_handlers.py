import pytest
from latex2json.nodes import DiagramNode
from latex2json.nodes.graphics_pdf_diagram_nodes import IncludeGraphicsNode
from latex2json.parser.parser import Parser


def test_picture_handler():
    parser = Parser()

    text = r"""
    \begin{picture}
    Hello
    \end{picture}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    assert out[0] == DiagramNode("picture", text)

    text = r"""
    \beginpicture
    Hello
    \endpicture
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    assert out[0] == DiagramNode("picture", text)


def test_overpic_handler():
    parser = Parser()

    text = r"""
    \begin{overpic}[width=0.5\textwidth]{example-image}
    \put(33,29){\tiny Faster R-CNN}
    \end{overpic} 
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], IncludeGraphicsNode)


def test_xymatrix_with_spaces():
    """Test xymatrix command with whitespace"""
    parser = Parser()
    text = r"""
\xymatrix{ A & B \\ C & D }
""".strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "xymatrix"
    assert diagram_node.diagram == text.strip()


def test_polylongdiv():
    """Test polylongdiv command with multiple braces"""
    parser = Parser()
    text = r"\polylongdiv{x^3 + 2x^2 + 3x + 4}{x + 1}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "polylongdiv"
    assert diagram_node.diagram == text.strip()


def test_xymatrix_with_at_options():
    """Test xymatrix with xy-pic @ options for spacing"""
    parser = Parser()
    text = r"\xymatrix@1@C+.5em{ A & B \\ C & D }"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "xymatrix"
    assert diagram_node.diagram == text.strip()

    text = r"\xymatrix@C=1pc@R+2em{ A \ar[r] & B }"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "xymatrix"
    assert diagram_node.diagram == text.strip()

    text = r"""
\xymatrix@=10em{
F(A_0)
\ar@<1ex>[r]^{F(f_4 f_3) F(f_2 f_1)}
\ar@<-1ex>[r]_{F(1_{A_4}) F(f_4) F(f_3 f_2) F(f_1)}     &
F(A_4)
}
""".strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "xymatrix"
    diagram_str = diagram_node.diagram.replace("\n", "").replace(" ", "")
    assert diagram_str == text.replace("\n", "").replace(" ", "")


def test_xymatrix_at_as_single_token():
    """Test xymatrix@ as a single token (makeatletter context)"""
    parser = Parser()
    # Simulate \xymatrix@ being treated as a single command token
    text = r"""\makeatletter
\xymatrix@C-2ex{ A & B }"""
    out = parser.parse(text)
    # Filter out whitespace nodes
    diagram_nodes = [n for n in out if isinstance(n, DiagramNode)]
    assert len(diagram_nodes) == 1
    diagram_node = diagram_nodes[0]
    assert diagram_node.env_name == "xymatrix"
    # Should preserve the full text including @C-2ex
    assert diagram_node.diagram == r"\xymatrix@C-2ex{ A & B }"


def test_pgfplotstabletypeset():
    """Test pgfplotstabletypeset command with optional bracket and required brace"""
    parser = Parser()
    text = r"\pgfplotstabletypeset[col sep=comma]{data.csv}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    diagram_node = out[0]
    assert diagram_node.env_name == "pgfplotstabletypeset"
    assert diagram_node.diagram == text.strip()
