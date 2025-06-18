from latex2json.expander.expander import Expander


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
