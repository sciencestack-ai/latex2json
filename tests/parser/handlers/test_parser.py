from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.include_graphics_pdf_nodes import IncludeGraphicsNode
from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes
from latex2json.parser.parser import Parser
from latex2json.nodes import EnvironmentNode, CaptionNode


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
