from latex2json.expander.expander import Expander
from latex2json.tokens.types import Token


def test_maketitle():

    expander = Expander()

    text = r"""
    \author{Yu Deng \xxx} % defer expansion until \maketitle
    \title{First title}
    \title{My title}

    \def\xxx{XXX}

    \maketitle
    """
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()

    # check that title is using the last one, and is the first thing in the string
    expected_strs = [r"\title{My title}", r"\author{Yu Deng XXX}"]

    check_str = out_str
    for expected_str in expected_strs:
        assert check_str.startswith(expected_str)
        check_str = check_str.replace(expected_str, "")
        check_str = check_str.strip()

    assert not check_str
