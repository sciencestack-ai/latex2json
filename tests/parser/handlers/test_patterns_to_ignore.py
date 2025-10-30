from latex2json.parser.parser import Parser


def test_patterns_to_ignore():
    parser = Parser()

    text = r"""
    \IEEEabstract
    \IEEEmembership
"""
    out = parser.parse(text)
    out_str = parser.convert_nodes_to_str(out).strip()
    assert out_str == ""
