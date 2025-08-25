import pytest
from latex2json.nodes import DiagramNode
from latex2json.parser.parser import Parser


def test_picture_handler():
    parser = Parser()

    text = r"""
    \begin{picture}
    Hello
    \end{picture}
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    assert out[0] == DiagramNode("picture", text)

    text = r"""
    \beginpicture
    Hello
    \endpicture
    """.strip()
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], DiagramNode)
    assert out[0] == DiagramNode("picture", text)
