from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_si():
    expander = Expander()
    out = expander.expand(r"\si{\metre\%} POST")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "m% POST"

    out = expander.expand(r"\SI{100}{\kilogram} POST")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "100kg POST"

    # check that \def\metre etc is ignored during si unit conversion
    expander.expand(r"\def\metre{METRE}")
    assert expander.expand(r"\metre") == expander.expand("METRE")
    # but in \si, not expanded to METRE
    assert expander.expand(r"\si{\metre}") == expander.expand("m")
