import pytest
from latex2json.nodes.base_nodes import TextNode
from latex2json.nodes.caption_node import CaptionNode
from latex2json.nodes.environment_nodes import (
    FigureNode,
    SubTableNode,
    SubFigureNode,
    TableNode,
)
from latex2json.nodes.graphics_pdf_diagram_nodes import IncludeGraphicsNode
from latex2json.nodes.utils import is_whitespace_node, strip_whitespace_nodes
from latex2json.parser.parser import Parser
from latex2json.registers.utils import int_to_alpha


def test_table_figure_handler():
    parser = Parser()

    text = r"""
    \begin{table}
    
    \begin{subtable}
    \caption{SUBCAPTION a} % caption numbered a
    \end{subtable}
    
    \begin{subfigure}
    \caption{SUBCAPTION b} % caption numbered b, even if subfigure under table
    \end{subfigure}

    \subfloat[SUBCAPTION c]{Body} % caption numbered c, converted as subtable

    \caption{Table Caption}

    \end{table}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], TableNode)
    # check that inner subfloat defaults to subtablenode if parent is table

    table_node = out[0]
    caption_node = table_node.get_caption_node()
    assert (
        caption_node
        and caption_node.numbering == "1"
        and caption_node.body == [TextNode("Table Caption")]
    )
    body = table_node.body

    subfigtable_nodes = [
        node for node in body if isinstance(node, (SubTableNode, SubFigureNode))
    ]

    N = 3
    assert len(subfigtable_nodes) == N
    for i in range(N):
        caption_node = subfigtable_nodes[i].get_caption_node()
        assert caption_node and caption_node.numbering == int_to_alpha(i + 1)


def test_subfigure_cmd_handler():
    parser = Parser()

    text = r"""
\begin{figure}[ht]
    \centering
    \subfigure[Fig A]{
        \includegraphics[width=0.54\textwidth]{figures/mmlu.pdf}
        \label{fig:mmlu}
    }
    \subfigure[Fig B]{
        \includegraphics[width=0.42\textwidth]{figures/efficiency.pdf}
        \label{fig:efficiency}
    }
    \label{fig:first_page}
    \caption{Figure Caption}
\end{figure}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], FigureNode)
    figure_node = out[0]
    assert figure_node.labels == ["fig:first_page"]
    caption_node = figure_node.get_caption_node()
    assert caption_node and caption_node.body == [TextNode("Figure Caption")]
    # strip whitespace nodes
    body = [node for node in figure_node.body if not is_whitespace_node(node)]
    assert len(body) == 3
    assert isinstance(body[0], SubFigureNode)
    assert isinstance(body[1], SubFigureNode)
    assert body[2] == caption_node
    assert isinstance(body[0], SubFigureNode)
    assert isinstance(body[1], SubFigureNode)

    subfig1 = body[0]
    assert subfig1.labels == ["fig:mmlu"]
    subfig1_caption = subfig1.get_caption_node()
    assert subfig1_caption and subfig1_caption.body == [TextNode("Fig A")]
    assert subfig1_caption.numbering == "a"
    sbody1 = [node for node in subfig1.body if not is_whitespace_node(node)]
    assert len(sbody1) == 2
    assert sbody1[0] == subfig1_caption
    assert sbody1[1] == IncludeGraphicsNode("figures/mmlu.pdf")

    subfig2 = body[1]
    assert subfig2.labels == ["fig:efficiency"]
    subfig2_caption = subfig2.get_caption_node()
    assert subfig2_caption and subfig2_caption.body == [TextNode("Fig B")]
    assert subfig2_caption.numbering == "b"
    sbody2 = [node for node in subfig2.body if not is_whitespace_node(node)]
    assert len(sbody2) == 2
    assert sbody2[0] == subfig2_caption
    assert sbody2[1] == IncludeGraphicsNode("figures/efficiency.pdf")
