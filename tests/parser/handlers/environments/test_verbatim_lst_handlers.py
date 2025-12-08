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


def test_minted_handler():
    parser = Parser()

    text = r"\begin{minted}[fontsize=\small, bgcolor=gray!10]{javascript}const x = 10;\end{minted}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode("const x = 10;", title="javascript")


def test_lstinputlisting_handler(tmp_path):
    """Test \\lstinputlisting command that reads code from a file"""
    parser = Parser()

    # Create a temporary Python file with code
    code_content = r"""\newcommand{test}{test}
def hello_world():
    print("Hello, World!")"""

    source_file = tmp_path / "source.py"
    source_file.write_text(code_content)

    # Set parser's project_root and cwd to tmp_path
    parser.project_root = str(tmp_path)
    parser.cwd = str(tmp_path)

    # Test basic usage without options
    text = r"\lstinputlisting{source.py}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode(code_content.strip(), title=None)

    # Test with language option
    text = r"\lstinputlisting[language=Python]{source.py}"
    out = parser.parse(text)
    assert len(out) == 1 and isinstance(out[0], VerbatimNode)
    assert out[0] == VerbatimNode(code_content.strip(), title="language=Python")


def test_lstinputlisting_missing_file():
    """Test \\lstinputlisting with non-existent file"""
    parser = Parser()

    text = r"\lstinputlisting{nonexistent.py}"
    out = parser.parse(text)
    # Should return empty list when file doesn't exist
    assert out == []


def test_lstinputlisting_with_real_files():
    """Test \\lstinputlisting loads actual Python and JavaScript files."""
    parser = Parser()
    parser.project_root = 'tests/samples/lstinputlisting_test'
    parser.cwd = 'tests/samples/lstinputlisting_test'

    with open('tests/samples/lstinputlisting_test/test_listings.tex') as f:
        text = f.read()

    nodes = parser.parse(text)

    # Helper to find all VerbatimNodes recursively
    def find_all_verbatim(nodes, results=None):
        if results is None:
            results = []
        for node in nodes:
            if isinstance(node, VerbatimNode):
                results.append(node)
            for attr in ['content', 'children', 'body']:
                if hasattr(node, attr):
                    value = getattr(node, attr)
                    if isinstance(value, list):
                        find_all_verbatim(value, results)
        return results

    verbatim_nodes = find_all_verbatim(nodes)

    # Should have at least 3 VerbatimNodes (one for each \lstinputlisting)
    assert len(verbatim_nodes) >= 3

    # Load expected content
    with open('tests/samples/lstinputlisting_test/example_code.py') as f:
        py_content = f.read().strip()

    with open('tests/samples/lstinputlisting_test/example_code.js') as f:
        js_content = f.read().strip()

    # Check Python file nodes
    py_nodes = [n for n in verbatim_nodes if 'Python' in (n.title or '')]
    assert len(py_nodes) >= 1
    assert py_nodes[0].text == py_content

    # Check JavaScript file nodes
    js_nodes = [n for n in verbatim_nodes if 'JavaScript' in (n.title or '')]
    assert len(js_nodes) >= 1
    assert js_nodes[0].text == js_content

    # Check node without language option
    no_lang_nodes = [n for n in verbatim_nodes if n.title is None]
    assert len(no_lang_nodes) >= 1
    assert no_lang_nodes[0].text == py_content
