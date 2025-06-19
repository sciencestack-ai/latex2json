from latex2json.expander.expander import Expander
from latex2json.tokens.utils import strip_whitespace_tokens


def test_column_handlers():
    expander = Expander()
    text = r"""
    \twocolumn[Stuff]
    \onecolumn
    """
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == expander.expand("Stuff")


def test_texorpdfstring_handler():
    expander = Expander()
    text = r"\texorpdfstring{pdf version}{text version}"
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)
    assert out == expander.expand("text version")


def test_head_handler():
    expander = Expander()

    test_cases = [
        (r"\fancyhead[R]{Simple text}", "Simple text"),
        (r"\fancyheadoffset{Simple text}", "Simple text"),
        (r"\rhead{Simple text}", "Simple text"),
        (r"\lhead{Raised text}", "Raised text"),
    ]

    for command, expected_text in test_cases:
        out = expander.expand(command)
        assert out == expander.convert_str_to_tokens(expected_text)
