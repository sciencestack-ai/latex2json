from typing import List, Tuple
import pytest

from latex2json.nodes import ASTNode, TextNode
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
                assert node.styles == exp_style
            index += 1

    assert index == len(expected_text_style_pairs)


def test_hl_default_color():
    r"""Test \hl{text} with default yellow color"""
    text = r"""
    \hl{highlighted text}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("highlighted text", ["highlight=yellow"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_sethlcolor():
    r"""Test \sethlcolor{color} to change highlight color"""
    text = r"""
    \definecolor{red}{rgb}{1,0,0}
    \sethlcolor{red}
    \hl{red highlight}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("red highlight", ["highlight=red"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_sethlcolor_with_rgb():
    r"""Test \sethlcolor with RGB color model"""
    text = r"""
    \sethlcolor[RGB]{0,255,0}
    \hl{green highlight}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("green highlight", ["highlight=rgb(0,255,0)"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_hl_nested_with_other_styles():
    r"""Test \hl nested with other text styles"""
    text = r"""
    \textbf{\hl{bold highlighted}}
    \hl{\textit{italic highlighted}}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("bold highlighted", ["bold", "highlight=yellow"]),
        ("italic highlighted", ["highlight=yellow", "italic"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_hl_with_textcolor():
    r"""Test \hl combined with \textcolor"""
    text = r"""
    \definecolor{red}{rgb}{1,0,0}
    \sethlcolor{cyan}
    \hl{\textcolor{red}{red text on cyan}}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("red text on cyan", ["highlight=cyan", "color=red"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_multiple_sethlcolor():
    """Test changing highlight color multiple times"""
    text = r"""
    \sethlcolor{yellow}
    \hl{yellow}
    \sethlcolor{magenta}
    \hl{magenta}
    \sethlcolor{cyan}
    \hl{cyan}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("yellow", ["highlight=yellow"]),
        ("magenta", ["highlight=magenta"]),
        ("cyan", ["highlight=cyan"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)


def test_hl_with_custom_definecolor():
    r"""Test \hl with custom defined colors"""
    text = r"""
    \definecolor{mycolor}{rgb}{0.5,0.5,0.5}
    \sethlcolor{mycolor}
    \hl{custom color}
    """.strip()

    parser = Parser()
    out = parser.parse(text)

    expected_text_style_pairs = [
        ("custom color", ["highlight=mycolor"]),
    ]

    assert_output_matches_expected(out, expected_text_style_pairs)
