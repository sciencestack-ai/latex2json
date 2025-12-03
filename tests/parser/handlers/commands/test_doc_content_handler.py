import pytest

from latex2json.nodes import (
    TextNode,
    MetadataNode,
    EnvironmentNode,
)
from latex2json.nodes.tabular_node import TabularNode
from latex2json.nodes.metadata_nodes import MaketitleNode
from latex2json.nodes.utils import strip_whitespace_nodes
from latex2json.parser.parser import Parser
from latex2json.expander.expander import Expander


@pytest.fixture
def parser():
    """Create a parser with no strictly blocked commands for all tests."""
    expander = Expander(strictly_blocked_commands=[])
    return Parser(expander=expander)


def test_doc_content_handler(parser: Parser):
    text = r"""
    \title{My Title}
    \author{John Doe \url{https://example.com}}
    %\author{some dude}
    \maketitle
    """.strip()
    out = parser.parse(text, postprocess=True)
    out = strip_whitespace_nodes(out)

    out = [n for n in out if not isinstance(n, TextNode)]

    # With new design, maketitle returns a MaketitleNode containing metadata
    assert len(out) == 1, "Should have one MaketitleNode"
    assert isinstance(out[0], MaketitleNode), "Should be a MaketitleNode"

    # Check that maketitle contains title and author metadata
    maketitle = out[0]
    metadata_children = [
        child for child in maketitle.children if isinstance(child, MetadataNode)
    ]

    title_nodes = [m for m in metadata_children if m.name == "title"]
    author_nodes = [m for m in metadata_children if m.name == "author"]

    assert len(title_nodes) == 1, "Should have title in maketitle"
    assert len(author_nodes) == 1, "Should have author in maketitle"
    assert title_nodes[0] == MetadataNode("title", [TextNode("My Title")])
    # assert out[1] == AuthorsNode(
    #     [
    #         AuthorNode(
    #             [
    #                 TextNode("John Doe "),
    #                 URLNode("https://example.com"),
    #             ]
    #         )
    #     ]
    # )

    # test some with brackets
    text = r"""\affil[1] {University of California, Los Angeles}"""
    out = parser.parse(text)
    assert out == [
        MetadataNode(
            "affiliation", [TextNode("University of California, Los Angeles")]
        ),
    ]


def test_appendices(parser: Parser):
    text = r"""
    \begin{appendices}
    APPENDIX A
    \end{appendices}
    """.strip()
    out = parser.parse(text)

    assert out == [MetadataNode("appendix", [TextNode("APPENDIX A")])]


def test_maketitle_with_alignauthor_edge_case(parser: Parser):
    """Test maketitle with \\alignauthor that contains \\end{tabular}\\begin{tabular}.

    This is an edge case where the author content contains sequential tabular
    environments that were previously causing the parser to incorrectly match
    environment boundaries, resulting in the abstract being absorbed into the
    first tabular environment.
    """
    text = r"""
\makeatletter
\def\@maketitle{
    \begin{tabular}[t]{c}\@author
    \end{tabular}
}
\def\maketitle{
    \@maketitle
}

\title{Caffe: Convolutional Architecture}

\def\alignauthor{
    \end{tabular}
  \begin{tabular}[t]{c}
}

\author{
    \alignauthor Yangqing Jia$^*$ \\
}

\maketitle

\begin{abstract}
Caffe Abstract
\end{abstract}
    """.strip()
    out = parser.parse(text, postprocess=True)
    out = strip_whitespace_nodes(out)

    # Filter to meaningful nodes
    out = [n for n in out if not isinstance(n, TextNode) or n.text.strip()]

    # With the new design, maketitle should be a MaketitleNode containing metadata children
    maketitle_nodes = [n for n in out if isinstance(n, MaketitleNode)]
    abstract_nodes = [
        n
        for n in out
        if (
            isinstance(n, EnvironmentNode)
            and getattr(n, "env_name", None) == "abstract"
        )
        or (isinstance(n, MetadataNode) and n.name == "abstract")
    ]

    assert len(maketitle_nodes) == 1, "Should have exactly one MaketitleNode"
    assert len(abstract_nodes) == 1, "Should have exactly one abstract node"

    # Verify the maketitle structure - user's custom @maketitle puts author in tabular
    maketitle = maketitle_nodes[0]

    # The user's custom @maketitle is: \begin{tabular}[t]{c}\@author\end{tabular}
    # So we expect a TabularNode child containing MetadataNode(author)
    tabular_in_maketitle = [
        child for child in maketitle.children if isinstance(child, TabularNode)
    ]
    assert (
        len(tabular_in_maketitle) >= 1
    ), "MaketitleNode should contain tabular from custom @maketitle"

    # Find author metadata somewhere in the maketitle tree (could be nested in tabular)
    def find_metadata_recursive(node, name):
        if isinstance(node, MetadataNode) and node.name == name:
            return True
        if hasattr(node, "children"):
            return any(find_metadata_recursive(child, name) for child in node.children)
        return False

    assert find_metadata_recursive(
        maketitle, "author"
    ), "MaketitleNode should contain author metadata"

    # Verify abstract is separate and NOT absorbed into maketitle
    abstract_text = abstract_nodes[0].detokenize().strip()
    maketitle_text = maketitle.detokenize()

    assert "Caffe Abstract" in abstract_text, "Abstract should contain 'Caffe Abstract'"
    assert (
        "Caffe Abstract" not in maketitle_text
    ), "Abstract should not be absorbed into maketitle"

    # The key bug this test checks: author content has \end{tabular}\begin{tabular}
    # which should NOT cause abstract to be absorbed
    assert "Yangqing Jia" in maketitle_text, "Maketitle should contain author name"
