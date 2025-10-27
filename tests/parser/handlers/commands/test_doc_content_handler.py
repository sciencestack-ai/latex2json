import pytest

from latex2json.nodes import (
    TextNode,
    MetadataNode,
    AuthorNode,
    AuthorsNode,
    URLNode,
)
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser


def test_doc_content_handler():
    parser = Parser()
    text = r"""
    \title{My Title}
    \author{John Doe \url{https://example.com}}
    %\author{some dude}
    \maketitle
    """.strip()
    out = parser.parse(text, postprocess=True)
    out = strip_whitespace_nodes(out)
    # assert out == []

    out = [n for n in out if not isinstance(n, TextNode)]

    assert len(out) == 2
    assert out[0] == MetadataNode("title", [TextNode("My Title")])
    assert out[1] == AuthorsNode(
        [
            AuthorNode(
                [
                    TextNode("John Doe "),
                    URLNode("https://example.com"),
                ]
            )
        ]
    )

    # test some with brackets
    text = r"""\affil[1] {University of California, Los Angeles}"""
    out = parser.parse(text)
    assert out == [
        MetadataNode(
            "affiliation", [TextNode("University of California, Los Angeles")]
        ),
    ]


def test_appendices():
    parser = Parser()
    text = r"""
    \begin{appendices}
    APPENDIX A
    \end{appendices}
    """.strip()
    out = parser.parse(text)

    assert out == [MetadataNode("appendix", [TextNode("APPENDIX A")])]
