import pytest

from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.nodes.ref_cite_url_nodes import CiteNode, RefNode, URLNode
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


# def test_label_outside_environment():
#     parser = Parser()

#     text = r"\label{standalone:label}"
#     out = parser.parse(text)

#     assert len(out) == 1
#     assert isinstance(out[0], CommandNode)
#     assert out[0].name == "label"


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


def test_cite():
    parser = Parser()

    text = r"\cite{sdsds,   ss}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], CiteNode)
    assert out[0].references == ["sdsds", "ss"]

    # test with pre/postnote
    text = r"\cites[see][Chapter 4]{sdsds, ss}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], CiteNode)
    assert out[0].references == ["sdsds", "ss"]
    assert out[0].title == "see, Chapter 4"

    # test prenote only
    text = r"\citep [Ch 5] {sdsds}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], CiteNode)
    assert out[0].references == ["sdsds"]
    assert out[0].title == "Ch 5"


def test_citealias():
    parser = Parser()

    text = r"\defcitealias{sdsds}{Ch 5}"
    out = parser.parse(text)

    assert len(out) == 0
    assert parser.cite_aliases == {"sdsds": "Ch 5"}

    text = r"\citetalias{sdsds}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], CiteNode)
    assert out[0].references == ["sdsds"]
    assert out[0].title == "Ch 5"

    # undefined citealias
    text = r"\citetalias{bbb}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], CiteNode)
    assert out[0].references == ["bbb"]
    assert out[0].title is None


def test_urls():
    parser = Parser()

    text = r"\url{https://www.google.com}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], URLNode)
    assert out[0].url == "https://www.google.com"

    text = r"\href {https://www.google.com} {Google}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], URLNode)
    assert out[0].url == "https://www.google.com"
    assert out[0].title == "Google"

    text = r"\doi {10.1000/182}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], URLNode)
    assert out[0].url == "https://doi.org/10.1000/182"
    assert out[0].title is None

    text = r"\path{https://www.google.com}"
    out = parser.parse(text)

    assert len(out) == 1
    assert isinstance(out[0], URLNode)
    assert out[0].url == "https://www.google.com"
    assert out[0].title is None
