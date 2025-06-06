from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_crefname():
    expander = Expander()
    out = expander.expand(r"\crefname{figure}{Figure}{Figures} POST")
    assert expander.check_tokens_equal(out, expander.expand(" POST"))
