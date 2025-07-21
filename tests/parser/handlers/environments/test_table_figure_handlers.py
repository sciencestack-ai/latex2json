import pytest
from latex2json.nodes.environment_nodes import SubTableNode, SubFigureNode, TableNode
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
    assert (
        table_node.get_caption_node() and table_node.get_caption_node().numbering == "1"
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
