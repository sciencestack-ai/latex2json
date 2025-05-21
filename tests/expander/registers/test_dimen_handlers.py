import pytest

from latex2json.expander.expander import Expander
from latex2json.expander.registers import RegisterType
from latex2json.tokens.utils import strip_whitespace_tokens
from latex2json.latex_maps.dimensions import dimension_to_scaled_points


def test_dimen_handler():
    expander = Expander()
    expander.expand(r"\dimen10=20pt")

    scaled_20pt = dimension_to_scaled_points(20, "pt")
    assert expander.get_register_value(RegisterType.DIMEN, 10) == scaled_20pt

    # requires \the handlers
    out = expander.expand(r"\the\dimen10")
    expected = expander.expand(
        str(scaled_20pt)
    )  # dimensions typically show with decimal
    assert expander.check_tokens_equal(out, expected)

    # test different units
    expander.expand(r"\dimen11=2.5cm")
    assert expander.get_register_value(
        RegisterType.DIMEN, 11
    ) == dimension_to_scaled_points(2.5, "cm")

    # test scope
    text = r"""
    {
        \global\dimen0 = 30mm
        \dimen4 = 40in
    }
    """
    expander.expand(text)

    scaled_30mm = dimension_to_scaled_points(30, "mm")
    scaled_40in = dimension_to_scaled_points(40, "in")
    assert expander.get_register_value(RegisterType.DIMEN, 0) == scaled_30mm
    assert not expander.get_register_value(RegisterType.DIMEN, 1)
    assert expander.check_tokens_equal(
        expander.expand(r"\the\dimen0"), expander.expand(str(scaled_30mm))
    )
    # default to 0pt
    assert expander.check_tokens_equal(
        expander.expand(r"\the\dimen4"), expander.expand("0")
    )


def test_newdimen():
    expander = Expander()
    expander.expand(r"\newdimen\mylength")
    assert expander.get_register_value(RegisterType.DIMEN, "mylength") == 0

    # test scope (newdimen is global)
    text = r"""
    {
        \newdimen\mylength % set 0pt by default
        \mylength= 15pt % this is local!
    }
    """
    expander.expand(text)
    assert expander.check_tokens_equal(
        expander.expand(r"\the\mylength"), expander.expand("0")
    )
    out = expander.expand(r"\mylength=25.5pt \the\mylength")
    scaled_25pt = dimension_to_scaled_points(25.5, "pt")
    assert expander.check_tokens_equal(
        strip_whitespace_tokens(out), expander.expand(str(scaled_25pt))
    )
