import pytest

from latex2json.expander.expander import Expander


def test_count_handler():
    expander = Expander()
    expander.expand(r"\count10=100")
    assert expander.get_register_value("count", 10) == 100

    # requires \the handlers
    out = expander.expand(r"\the\count10")
    expected = expander.expand("100")
    assert expander.check_tokens_equal(out, expected)


def test_count_scope():
    expander = Expander()

    text = r"""
    {
        \global\count0 = 100
        \count1 = 200
    }
    """
    expander.expand(text)
    assert expander.get_register_value("count", 0) == 100
    assert not expander.get_register_value("count", 1)
    assert expander.check_tokens_equal(
        expander.expand(r"\the\count0"), expander.expand("100")
    )
    # default to 0
    assert expander.check_tokens_equal(
        expander.expand(r"\the\count1"), expander.expand("0")
    )
