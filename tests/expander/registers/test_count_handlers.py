import pytest

from latex2json.expander.expander import Expander
from latex2json.expander.registers import RegisterType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_count_handler():
    expander = Expander()
    expander.expand(r"\count10=100")
    assert expander.get_register_value(RegisterType.COUNT, 10) == 100

    # requires \the handlers
    out = expander.expand(r"\the\count10")
    expected = expander.expand("100")
    assert expander.check_tokens_equal(out, expected)

    # test scope
    text = r"""
    {
        \global\count0 = 100
        \count1 = 200
    }
    """
    expander.expand(text)
    assert expander.get_register_value(RegisterType.COUNT, 0) == 100
    assert not expander.get_register_value(RegisterType.COUNT, 1)
    assert expander.check_tokens_equal(
        expander.expand(r"\the\count0"), expander.expand("100")
    )
    # default to 0
    assert expander.check_tokens_equal(
        expander.expand(r"\the\count1"), expander.expand("0")
    )


def test_newcount():
    expander = Expander()
    expander.expand(r"\newcount\mycounter")
    assert expander.get_register_value(RegisterType.COUNT, "mycounter") == 0

    # test scope (newcount is global)
    text = r"""
    {
        \newcount\mycounter % set 0 by default
        \mycounter= 100 % this is local! 
    }
    """
    expander.expand(text)
    assert expander.check_tokens_equal(
        expander.expand(r"\the\mycounter"), expander.expand("0")
    )
    out = expander.expand(r"\mycounter=100 \the\mycounter")
    assert expander.check_tokens_equal(
        strip_whitespace_tokens(out), expander.expand("100")
    )
