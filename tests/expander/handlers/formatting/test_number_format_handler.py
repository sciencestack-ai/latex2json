from latex2json.expander.expander import Expander
from latex2json.registers.utils import int_to_roman


def test_number_handler():
    expander = Expander()

    text = r"\setcounter{section}{10}\number \value{section}"
    out = expander.expand(text)
    assert expander.check_tokens_equal(out, expander.expand("10"))


def test_num_handler():
    expander = Expander()

    text = r"\num{1.234567890}"
    out = expander.expand(text)
    assert expander.check_tokens_equal(out, expander.expand("1.23456789"))

    text = r"\num[round-precision=2]{1.234567890}"
    out = expander.expand(text)
    assert expander.check_tokens_equal(out, expander.expand("1.23"))

    text = r"\num[round-precision=2]{1.23456789}999"
    out = expander.expand(text)
    assert expander.check_tokens_equal(out, expander.expand("1.23999"))


def test_romannumeral_handler():
    expander = Expander()

    # works with braces
    text = r"\romannumeral{123}"
    out = expander.expand(text)
    assert expander.check_tokens_equal(out, expander.expand(int_to_roman(123)))

    # works without braces (does not work with .)
    text = r"\romannumeral1000.3"
    out = expander.expand(text)
    assert expander.check_tokens_equal(out, expander.expand(int_to_roman(1000) + ".3"))

    # works with negative numbers (but consumes them, does not show in latex)
    text = r"\romannumeral-123"
    out = expander.expand(text)
    assert out == []
