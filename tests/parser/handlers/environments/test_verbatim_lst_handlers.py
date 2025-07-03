import pytest
from latex2json.nodes import VerbatimNode
from latex2json.nodes.base_nodes import TextNode
from latex2json.parser.parser import Parser


def test_verbatim_handler():
    parser = Parser()

    text = r"\begin{verbatim}Hello\end {fake} \end{verbatim}POST"
    out = parser.parse(text)
    assert len(out) == 2 and isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode(r"Hello\end {fake}")
    assert out[1] == TextNode("POST")


def test_lstlisting_handler():
    parser = Parser()

    body = r"\newcommand{test}{test}"
    text = r"\begin{lstlisting}[language=Python]%s\end{lstlisting}" % (body)
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode(body, title="language=Python")
