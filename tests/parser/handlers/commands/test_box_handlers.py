import pytest
from typing import List, Tuple

from latex2json.nodes import TextNode, EquationNode, TabularNode
from latex2json.nodes.ref_cite_url_nodes import CiteNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser
from latex2json.registers.defaults.boxes import KATEX_SUPPORTED_BOXES


def test_box_commands():
    parser = Parser()

    # Test that box commands only return their text content
    test_cases = [
        (r"\hbox to 3in{Some text}", "Some text"),
        (r"\makebox{Simple text}", "Simple text"),
        (r"\framebox{Simple text}", "Simple text"),
        (r"\raisebox{2pt}{Raised text}", "Raised text"),
        (r"\raisebox{2pt}[1pt][2pt]{Raised text}", "Raised text"),
        (r"\makebox[3cm]{Fixed width}", "Fixed width"),
        (r"\framebox[3cm][l]{Left in frame}", "Left in frame"),
        (r"\parbox{5cm}{Simple parbox text}", "Simple parbox text"),
        (r"\parbox[t][3cm][s]{5cm}{Stretched vertically}", "Stretched vertically"),
        (r"\resizebox{\textwidth}{!}{RESIZE}", "RESIZE"),
        (r"\fbox{Framed text}", "Framed text"),
        (r"\colorbox{yellow}{Colored box}", "Colored box"),
        (
            r"\parbox[c][3cm]{5cm}{Center aligned with fixed height}",
            "Center aligned with fixed height",
        ),
        (
            r"""\mbox{
            All One line ajajaja
            
            }""",
            "All One line ajajaja",
        ),
        (r"\pbox{3cm}{Some text}", "Some text"),
        (r"\adjustbox{max width=\textwidth}{Some text}", "Some text"),
        (r"\rotatebox{90}{Some text}", "Some text"),
    ]

    # text mode only
    for command, expected_text in test_cases:
        out = parser.parse(command)
        out_str = parser.convert_nodes_to_str(out)
        assert out_str == expected_text

    # but also check that nodes are not unnecessarily converted to text nodes
    text = r"""
\resizebox{\textwidth}{!}{
\begin{tabular}{c}
111 & 222
\end{tabular}
}
""".strip()
    out = parser.parse(text)
    out = strip_whitespace_nodes(out)
    assert len(out) == 1 and isinstance(out[0], TabularNode)


def test_box_commands_in_mathmode():
    parser = Parser()

    # now try math mode

    # raisebox is katex supported
    assert "raisebox" in KATEX_SUPPORTED_BOXES

    text = r"""$\raisebox{1in}[]{sometext$1+1$}$"""
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    assert out[0].body == [TextNode("\\raisebox{1in}{sometext$1+1$}")]

    # mbox is not katex supported, so convert to hbox
    assert "mbox" not in KATEX_SUPPORTED_BOXES
    text = r"""$\mbox{sometext$1+1$}$"""
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    assert out[0].body == [TextNode("\\hbox{sometext$1+1$}")]

    # but also check that \ref\cite etc tokens are not converted to raw str
    # the box decorator is wrapped around all text + inner equations, but not around \ref\cite etc
    text = r"$$\raisebox{1in}{abc \cite{ref1}$123$}$$"  # -> \textbf{abc }, citenode, \textbf{$123$},
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    eq = out[0]
    assert len(eq.children) == 3

    assert eq.children[0] == TextNode(r"\raisebox{1in}{abc }")
    assert eq.children[1] == CiteNode("ref1")
    assert eq.children[2] == TextNode(r"\raisebox{1in}{$123$}")
