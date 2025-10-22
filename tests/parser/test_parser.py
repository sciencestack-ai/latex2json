from typing import List
from latex2json.nodes import DisplayType, TextNode, VerbatimNode, IncludeGraphicsNode
from latex2json.nodes.bibliography_nodes import BibEntryNode
from latex2json.nodes.environment_nodes import TheoremNode
from latex2json.nodes.list_item_node import ListNode
from latex2json.nodes.math_nodes import EquationNode
from latex2json.nodes.ref_cite_url_nodes import RefNode
from latex2json.nodes.section_nodes import SectionNode
from latex2json.nodes.utils import (
    find_nodes_by_type,
    is_whitespace_node,
    strip_whitespace_nodes,
)
from latex2json.parser.parser import Parser
from latex2json.nodes import EnvironmentNode, CaptionNode

import os


def test_quotes():
    parser = Parser()
    text = r"""
    `single quote' ``double quote''
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], TextNode)
    expected = "'single quote' " + '"double quote"'
    assert out[0].text == expected


def test_labels_n_captions_n_figures():
    parser = Parser()
    text = r"""
    \begin{figure}
        \caption{Figure 1}
        \label{cap:fig1}
        \includegraphics{example.pdf}
    \end{figure}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], EnvironmentNode)

    figure_node = out[0]
    assert figure_node.name == "figure"
    figure_body = [node for node in figure_node.body if not is_whitespace_node(node)]
    assert len(figure_body) == 2
    assert isinstance(figure_body[0], CaptionNode)
    caption_node = figure_body[0]
    assert caption_node == CaptionNode(
        body=[TextNode("Figure 1")], numbering="1", counter_name="figure"
    )

    assert figure_body[1] == IncludeGraphicsNode("example.pdf")

    # label belongs to caption!
    assert caption_node.labels == ["cap:fig1"]
    assert figure_node.labels == []

    assert parser.current_env is None

    # test with minipage/captionof
    text = r"""
    \begin{minipage}{0.45\textwidth}
        %\centering
        \includegraphics[width=0.5\textwidth]{example-image}
        \captionof{figure}{Example Image}
        \label{cap:fig2}
    \end{minipage}
    """.strip()

    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], EnvironmentNode)
    minipage_node = out[0]
    assert minipage_node.name == "minipage"
    minipage_body = [
        node for node in minipage_node.body if not is_whitespace_node(node)
    ]
    assert len(minipage_body) == 2

    assert minipage_body[0] == IncludeGraphicsNode("example-image")
    captionof_node = minipage_body[1]
    assert captionof_node == CaptionNode(
        body=[TextNode("Example Image")],
        numbering="2",
        opt_arg=[TextNode("Figure 2")],  # opt arg is env name + numbering
        counter_name="figure",
    )

    assert captionof_node.labels == ["cap:fig2"]
    assert minipage_node.labels == []

    assert parser.current_env is None


def test_verbatim_handler():
    parser = Parser()

    # verb
    text = r"""
    \verb+Hello+
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode("Hello", display=DisplayType.INLINE)

    # lstinline
    text = r"""
    \lstinline[language=Python]|Hello|
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode(
        "Hello", display=DisplayType.INLINE, title="language=Python"
    )


def test_theorem_handler():
    parser = Parser()
    text = r"""
    \newtheorem{theorem}{Theorem}
    \begin{theorem}[Estimate for the gradient]
    Hello
    \end{theorem}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], TheoremNode)
    assert out[0] == TheoremNode(
        "theorem",
        title=[TextNode("Estimate for the gradient")],
        body=[TextNode("Hello")],
        numbering="1",
        display_name="Theorem",
    )


def test_equation_tag_numbering_n_sanitization():
    parser = Parser()
    text = r"""
    \begin{equation}
    \label{eq:psi} \tag{\textbf{P}}
    \end{equation}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], EquationNode)
    assert out[0].numbering == "P"

    text = r"""$$ 1+1 \eqno(1.1) $$"""
    out = parser.parse(text)
    assert len(out) == 1
    assert isinstance(out[0], EquationNode)
    assert out[0].numbering == "1.1"


SAMPLES_DIR_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "../samples"
)


def test_parse_file():
    parser = Parser()

    out = parser.parse_file(os.path.join(SAMPLES_DIR_PATH, "main.tex"))
    out = strip_whitespace_nodes(out)
    assert len(out) >= 1
    # assert isinstance(out[0], EnvironmentNode)
    # assert out[0].name == "document"
    # assert len(out[0].body) == 2
    # assert out[0].body[0].name == "subfile"
    # assert out[0].body[1].name == "subfile"


def test_subfiles_and_external_documents_reference_resolution():
    parser = Parser()

    filepath = os.path.join(SAMPLES_DIR_PATH, "subfiles/manuscript.tex")
    nodes = parser.parse_file(
        filepath, postprocess=True, resolve_cross_document_references=True
    )
    nodes = strip_whitespace_nodes(nodes)
    assert len(nodes) >= 1

    # first, check the refs are apprioriately resolved with relevant file prefixes
    ref_nodes: List[RefNode] = find_nodes_by_type(nodes, RefNode)

    expected_refs_n_sourcefile = [
        (["manuscript:sec:main"], "manuscript.tex"),
        (["manuscript:sec:main"], "intro.tex"),
        (["intro:sec:intro"], "intro.tex"),
        (["intro:M-sec:fake"], "intro.tex"),
        (["intro:sec:intro", "manuscript:sec:main"], "appendix.tex"),
    ]

    assert len(ref_nodes) == len(expected_refs_n_sourcefile)
    for i, ref_node in enumerate(ref_nodes):
        exp = expected_refs_n_sourcefile[i]
        assert ref_node.references == exp[0]
        assert ref_node.get_source_file() == exp[1]

    # then check that node labels are also apprioriately resolved
    sec_nodes: List[SectionNode] = find_nodes_by_type(nodes, SectionNode)
    expected_sec_labels_n_sourcefile = [
        (["manuscript:sec:main"], "manuscript.tex"),
        (["intro:sec:intro"], "intro.tex"),
        (["intro:M-sec:fake"], "intro.tex"),
        (["appendix:sec:appendix"], "appendix.tex"),
    ]

    assert len(sec_nodes) == len(expected_sec_labels_n_sourcefile)
    for i, sec_node in enumerate(sec_nodes):
        exp = expected_sec_labels_n_sourcefile[i]
        assert sec_node.labels == exp[0]
        assert sec_node.get_source_file() == exp[1]


def test_postprocessing():
    parser = Parser()
    # check that postprocessing converts e.g. \& -> &, \@ -> "", but NOT in mathmode
    text = r"""
    \& $\&$ \@\# 
    """.strip()
    out = parser.parse(text, postprocess=True)
    out_str = parser.convert_nodes_to_str(out).strip()
    assert out_str == r"& $\&$ #"


def test_with_bib():
    parser = Parser()
    filepath = os.path.join(SAMPLES_DIR_PATH, "test_with_bib.tex")
    nodes = parser.parse_file(filepath, postprocess=True)
    nodes = strip_whitespace_nodes(nodes)
    assert len(nodes) >= 1

    # check that the bib entries are parsed
    bib_nodes: List[BibEntryNode] = find_nodes_by_type(nodes, BibEntryNode)
    assert len(bib_nodes) >= 1


def test_newlist():
    text = r"""
\newlist{inlinelist}{itemize*}{1}
\setlist[inlinelist,1]{label=(\roman*)} % ignored
\begin{inlinelist}
    \item Item 1
    \item Item 2
\end{inlinelist}
""".strip()
    parser = Parser()
    out = parser.parse(text)
    out = strip_whitespace_nodes(out)
    assert len(out) == 1
    assert isinstance(out[0], ListNode)
    list_node = out[0]
    assert list_node.list_type == "itemize"
    assert list_node.is_inline == True
    assert len(list_node.list_items) == 2
