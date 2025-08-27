from latex2json.expander.expander import Expander


def test_insert():
    expander = Expander()

    expander.expand(r"\newinsert\myins")

    # test \insert
    out = expander.expand(r"\insert\myins{abc}")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == ""

    # test \insert\footins{...} becomes \footnote{...}
    out = expander.expand(r"\insert\footins{abc}")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"\footnote{abc}"
