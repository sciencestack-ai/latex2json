import pytest

from latex2json.expander.expander import Expander
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from tests.test_utils import assert_token_sequence


def test_advance_handler():

    expander = Expander()

    expander.expand(r"\newcount\mycount")
    expander.expand(r"\advance\mycount by 10")
    assert_token_sequence(expander.expand(r"\the\mycount"), expander.expand("10"))

    # test \advance on nested macro
    expander.expand(r"\def\cnter{\count} \def\one{1}")
    expander.expand(r"\advance\cnter\one by 20")
    assert_token_sequence(expander.expand(r"\the\cnter\one"), expander.expand("20"))

    # test \advance on optional [by] and whitespaces
    expander.expand(r"\advance \mycount  -10")
    # 10 - 10 = 0
    assert_token_sequence(expander.expand(r"\the\mycount"), expander.expand("0"))

    expander.expand(r"\def\cnttwo{\count2}")
    expander.expand(r"\advance \cnttwo  22")
    assert_token_sequence(expander.expand(r"\the\cnttwo"), expander.expand("22"))
    assert_token_sequence(expander.expand(r"\the\count2"), expander.expand("22"))

    # test on dimensions
    expander.expand(r"\newdimen\mydimen")
    expander.expand(r"\advance \mydimen by 10pt")
    pt10_to_sp = dimension_to_scaled_points(10, "pt")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.convert_str_to_tokens(str(pt10_to_sp)),
    )

    expander.expand(r"\advance \mydimen by -10pt")
    assert_token_sequence(expander.expand(r"\the\mydimen"), expander.expand("0"))

    # test with increment as macro
    expander.expand(r"\def\incrtenpt{10pt}")
    expander.expand(r"\advance \mydimen by \incrtenpt")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.convert_str_to_tokens(str(pt10_to_sp)),
    )

    expander.expand(r"\advance \mydimen by -\incrtenpt")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.expand("0"),
    )

    # test with args
    text = r"""
    \def\advanceby#1->#2{\advance #1 by #2}
    \def\TEN{10}
    \newcount\cntx
    \advanceby\cntx->\TEN

    \advanceby\count100->100
    """
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\the\cntx"), expander.expand("10"))
    assert_token_sequence(expander.expand(r"\the\count100"), expander.expand("100"))

    # test advanceby with register themselves as increment
    expander.expand(r"\advanceby\count100->{ -\count100 }")
    assert_token_sequence(expander.expand(r"\the\count100"), expander.expand("0"))

    # slightly more complex nestings
    text = r"""
    \count2=100
    \def\neg#1{-#1}
    \advanceby\count2->-\neg{\count2} % → --200 = +200
    """
    expander.expand(text)
    assert_token_sequence(expander.expand(r"\the\count2"), expander.expand("200"))


def test_advance_handler_with_dimension_unit():
    expander = Expander()
    expander.expand(r"\newdimen\mydimen")
    expander.expand(r"\advance \mydimen by 10pt")
    pt_10 = dimension_to_scaled_points(10, "pt")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.expand(str(pt_10)),
    )

    # test with multiplier
    expander.expand(r"\advance \mydimen by 0.5\mydimen")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.expand(str(int(pt_10 + 0.5 * pt_10))),
    )

    # set back to 0 via \advance ... by -\mydimen
    expander.expand(r"\advance \mydimen by -\mydimen")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.expand("0"),
    )

    # set back to 10 pt
    expander.expand(r"\advance \mydimen by 10 pt")
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.expand(str(pt_10)),
    )

    # test with \def
    expander.expand(r"\def\defmydimen{\mydimen}")
    # add by 0.5 of \defmydimen -> \mydimen = 0.5 * 10 pt = 5 pt
    out = expander.expand(r"\advance \mydimen by 0.5\defmydimen")
    assert out == []
    assert_token_sequence(
        expander.expand(r"\the\mydimen"),
        expander.expand(str(int(pt_10 + 0.5 * pt_10))),
    )

    expander.expand(r"\def\tenpoints{10pt}")
    # actually in latex, this won't even work. \tenpoints just becomes consumed and not assigned
    out = expander.expand(r"\advance \mydimen by 0.5\tenpoints")
    assert out == []
    # assert_token_sequence(
    #     expander.expand(r"\the\mydimen"),
    #     expander.expand(str(int(pt_10 + pt_10))),
    # )


def test_advance_handler_with_box_dimension():
    expander = Expander()
    expander.expand(r"\newbox\mybox")
    expander.expand(r"\setbox\mybox=\hbox{Hello}")
    expander.expand(r"\advance \wd\mybox by -10pt")

    pt_10 = dimension_to_scaled_points(10, "pt")
    assert_token_sequence(
        expander.expand(r"\the\wd\mybox"),
        expander.expand(str(-pt_10)),
    )


def test_multiply_divide_handler():
    expander = Expander()
    expander.expand(r"\newcount\mycount")
    expander.expand(r"\advance \mycount by 10")
    assert_token_sequence(expander.expand(r"\the\mycount"), expander.expand("10"))

    expander.expand(r"\divide \mycount by 2")
    assert_token_sequence(expander.expand(r"\the\mycount"), expander.expand("5"))

    expander.expand(r"\multiply \mycount by 2")
    assert_token_sequence(expander.expand(r"\the\mycount"), expander.expand("10"))
