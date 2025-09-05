from typing import List, Tuple
import pytest

from latex2json.nodes import ASTNode, TextNode, EquationNode, CiteNode
from latex2json.parser.parser import Parser


def assert_output_matches_expected(
    out: List[ASTNode], expected_text_style_pairs: List[Tuple[str, List[str]]]
):
    index = 0
    for node in out:
        assert isinstance(node, TextNode)
        if not node.is_whitespace():
            exp_text, exp_style = expected_text_style_pairs[index]
            assert node.text.strip() == exp_text
            if node.styles:
                assert (
                    node.styles
                    == exp_style
                    # if exp_style and exp_style != "normal"
                    # else []
                )
            index += 1

    assert index == len(expected_text_style_pairs)


def test_text_handlers():
    text = r"""
    \definecolor{red}{rgb}{1,0,0}
    \textcolor{red}{RED}
    \textbf{Bold text}
    \textit{Italic text}
    \texttt{Monospace text}
    \textsuperscript{superscript}
    \underline{underlined text}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("RED", ["color=red"]),
        ("Bold text", ["bold"]),
        ("Italic text", ["italic"]),
        ("Monospace text", ["monospace"]),
        ("superscript", ["superscript"]),
        ("underlined text", ["underline"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_legacy_text_handlers():
    text = r"""
    \font\userfont = cmr10
    {\bf BOLD}
    {\it ITALIC}
    {\tt MONOSPACE}
    {\sc SMALL CAPS}
    {\sf SANS SERIF}
    {\rm ROMAN}
    {\em EMPH}
    {\userfont user font}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("BOLD", ["bold"]),
        ("ITALIC", ["italic"]),
        ("MONOSPACE", ["monospace"]),
        ("SMALL CAPS", ["small-caps"]),
        ("SANS SERIF", ["sans-serif"]),
        ("ROMAN", ["normal"]),
        ("EMPH", ["italic"]),
        ("user font", []),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_nested_text_styles():
    text = r"""
    \textbf{\textit{Bold Italic}}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    assert out == [
        TextNode("Bold Italic"),
    ]
    assert out[0].styles == ["bold", "italic"]

    #     # notice \bf + shape(\it vs \sc) switches on/off
    #     text = r"""
    #     {\bf BOLD \it BOLD-ITALIC \sc BOLD-SC \it BOLD-ITALIC \it BOLD \bf NORMAL}
    #     {\color{blue} BLUE \color{blue} NONBLUE \color[rgb]{1,0,0} RED \normalcolor NONRED}
    # """.strip()
    #     out = parser.parse(text)

    #     expected_text_style_pairs = [
    #         ("BOLD", ["bold"]),
    #         ("BOLD-ITALIC", ["bold", "italic"]),
    #         ("BOLD-SC", ["bold", "small-caps"]),
    #         ("BOLD-ITALIC", ["bold", "italic"]),
    #         ("BOLD", ["bold"]),
    #         ("NORMAL", []),
    #         ("BLUE", ["color=blue"]),
    #         ("NONBLUE", []),
    #         ("RED", ["color=rgb(255, 0, 0)"]),  # converted to css
    #         ("NONRED", []),
    #     ]

    #     assert_output_matches_expected(out, expected_text_style_pairs)


#     text = r"""
#     {
#         \bf {\it {\color{green} BOLD-ITALIC-GREEN} BOLD-ITALIC }
#         BOLD
#     }
#     POST
# """
#     out = parser.parse(text)
#     expected_text_style_pairs = [
#         ("BOLD-ITALIC-GREEN", ["bold", "italic", "color=green"]),
#         ("BOLD-ITALIC", ["bold", "italic"]),
#         ("BOLD", ["bold"]),
#         ("POST", []),
#     ]
#     assert_output_matches_expected(out, expected_text_style_pairs)


def test_citetext():
    text = r"""
    \citetext{My Text}
    """.strip()
    parser = Parser()
    out = parser.parse(text)
    assert out == [TextNode("My Text")]


def test_backslash_indent():
    text = r"""
    \backslash
    """.strip()
    parser = Parser()
    out = parser.parse(text)
    assert out == [TextNode(r"\\")]


def test_textmode_inside_math():
    text = r"$$1+1 \textbf{aa $1+1$ bb} 2+2$$"
    parser = Parser()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)

    # check that the text part is rolled out as raw str in equation node
    eq_str = out[0].equation_to_str()
    assert eq_str == r"1+1 \textbf{aa $1+1$ bb} 2+2"

    # but also check that \ref\cite etc tokens are not converted to raw str
    # the text decorator is wrapped around all text + inner equations, but not around \ref\cite etc
    text = r"$$\textbf{abc \cite{ref1}$123$}$$"  # -> \textbf{abc }, citenode, \textbf{$123$},
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], EquationNode)
    eq = out[0]
    assert len(eq.children) == 3

    assert eq.children[0] == TextNode(r"\textbf{abc }")
    assert eq.children[1] == CiteNode("ref1")
    assert eq.children[2] == TextNode(r"\textbf{$123$}")


def test_say_handler():
    text = r"""
    \say{hello}
    """.strip()
    parser = Parser()
    out = parser.parse(text)
    out_str = parser.convert_nodes_to_str(out).strip()
    assert out_str == '"hello"'
