from latex2json.nodes import DisplayType, TextNode, VerbatimNode, IncludeGraphicsNode
from latex2json.nodes.environment_nodes import TheoremNode
from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes
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
    assert caption_node == CaptionNode(body=[TextNode("Figure 1")], numbering="1")

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


def test_parse_file():
    parser = Parser()

    dir_path = os.path.dirname(os.path.abspath(__file__))
    sample_dir_path = os.path.join(dir_path, "../samples")
    out = parser.parse_file(os.path.join(sample_dir_path, "main.tex"))
    out = strip_whitespace_nodes(out)
    assert len(out) == 1
    # assert isinstance(out[0], EnvironmentNode)
    # assert out[0].name == "document"
    # assert len(out[0].body) == 2
    # assert out[0].body[0].name == "subfile"
    # assert out[0].body[1].name == "subfile"
