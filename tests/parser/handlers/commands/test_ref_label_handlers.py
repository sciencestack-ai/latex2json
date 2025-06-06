import pytest

from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.ref_node import RefNode
from latex2json.nodes.tabular_node import TabularNode
from latex2json.parser.parser import Parser


def test_basic_ref_commands():
    parser = Parser()

    # Test different ref commands
    ref_commands = ["ref", "autoref", "eqref", "pageref"]

    # ensure preserve whitespace and commas! This is NOT cref
    for cmd in ref_commands:
        text = f"\\{cmd}{{ test:label, ss}}"
        out = parser.parse(text)

        assert len(out) == 1
        assert isinstance(out[0], RefNode)
        assert out[0].references == [" test:label, ss"]


def test_cref_with_comma_split():
    parser = Parser()

    text = r"\cref{fig:1,fig:2, fig:3}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], RefNode)
    assert out[0].references == ["fig:1", "fig:2", " fig:3"]


def test_hyperref():
    parser = Parser()

    text = r"\hyperref[sec:intro]{Introduction Section}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], RefNode)
    assert out[0].references == ["sec:intro"]
    assert out[0].title == "Introduction Section"


def test_label_in_environment():
    parser = Parser()

    text = r"""
    \begin{tabular}{c}
        \label{tab:example}
        Content & More content \\
    \end{tabular}
    """.strip()

    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], TabularNode)
    assert out[0].labels == ["tab:example"]


def test_label_outside_environment():
    parser = Parser()

    text = r"\label{standalone:label}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], CommandNode)
    assert out[0].name == "label"


def test_ref_with_asterisk():
    parser = Parser()

    text = r"\ref*{fig:example}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], RefNode)
    assert out[0].references == ["fig:example"]


def test_empty_ref():
    parser = Parser()

    text = r"\ref{}"
    out = parser.parse(text)

    assert len(out) == 0  # Empty ref should return empty list
