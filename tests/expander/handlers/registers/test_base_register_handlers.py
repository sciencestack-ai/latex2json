from latex2json.expander.expander import Expander
from latex2json.latex_maps.counts import BUILTIN_COUNTS
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.registers import RegisterType
from latex2json.latex_maps.dimensions import BUILTIN_DIMENSIONS
from latex2json.registers.types import Box
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import strip_whitespace_tokens


def test_register_macros():
    expander = Expander()

    for register_type in RegisterType:
        if (
            register_type != RegisterType.BOX and register_type != RegisterType.BOOL
        ):  # handle box separately due to \setbox
            assert expander.get_macro(register_type.value)

    # test on dim direct expand
    expander.expand(r"\dimen20=10pt")
    assert expander.get_register_value(RegisterType.DIMEN, 20) > 0

    # does not expand by itself
    out = expander.expand(r"\dimen20")
    assert expander.check_tokens_equal(
        out,
        [
            Token(TokenType.CONTROL_SEQUENCE, "dimen"),
            Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
            Token(TokenType.CHARACTER, "0", catcode=Catcode.OTHER),
        ],
    )


def test_builtin_dimens():
    expander = Expander()

    expander.expand(r"\makeatletter")

    # e.g. \textwidth, \textheight, \parindent, etc
    for builtin_dimen in BUILTIN_DIMENSIONS:
        expander.expand(f"\\{builtin_dimen}=10pt")
        assert expander.get_register_value(RegisterType.DIMEN, builtin_dimen) > 0

        # also test regular without = assignment e.g. \parindent 10pt
        out = expander.expand(f"\\{builtin_dimen} 10pt")
        assert out == []


def test_builtin_counts():
    expander = Expander()
    for builtin_count in BUILTIN_COUNTS:
        out = expander.expand(f"\\{builtin_count}=10")
        assert out == []
        assert expander.get_register_value(RegisterType.COUNT, builtin_count) == 10


def test_new_register_macros():
    expander = Expander()

    # count
    expander.expand(r"\newcount\mycount")
    assert expander.get_register_value(RegisterType.COUNT, "mycount") == 0
    assert expander.check_macro_is_user_defined("mycount")

    expander.expand(r"\mycount=10")
    assert expander.get_register_value(RegisterType.COUNT, "mycount") == 10

    # dimen
    expander.expand(r"\newdimen\mydimen")
    assert expander.get_register_value(RegisterType.DIMEN, "mydimen") == 0

    expander.expand(r"\mydimen=10pt")
    assert expander.get_register_value(RegisterType.DIMEN, "mydimen") > 0

    # skip
    expander.expand(r"\newskip\myskip")
    assert expander.get_register_value(RegisterType.SKIP, "myskip") == 0

    expander.expand(r"\myskip=10pt")
    assert expander.get_register_value(RegisterType.SKIP, "myskip") > 0

    # muskip
    expander.expand(r"\newmuskip\mymuskip")
    assert expander.get_register_value(RegisterType.MUSKIP, "mymuskip") == 0

    expander.expand(r"\mymuskip=10pt")
    assert expander.get_register_value(RegisterType.MUSKIP, "mymuskip") > 0

    # toks
    expander.expand(r"\newtoks\mytoks")
    assert expander.get_register_value(RegisterType.TOKS, "mytoks") == []

    expander.expand(r"\mytoks={abc}")
    assert expander.get_register_value(RegisterType.TOKS, "mytoks") == expander.expand(
        "abc"
    )


def test_toks():
    expander = Expander()

    expander.expand(r"\newtoks\mytoks")
    out = expander.expand(r"\mytoks={abc}")
    assert len(out) == 0

    out = expander.expand(r"\the\mytoks")
    assert expander.check_tokens_equal(out, expander.expand("abc"))

    # test in scope (the new registers are global, but assignments are local)
    text = r"""
        \newtoks\tokker
        \tokker={123}
        \the\tokker
    """.strip()
    expander.push_scope()
    out = expander.expand(text)
    out = strip_whitespace_tokens(out)

    tokens_123 = expander.expand("123")
    assert expander.check_tokens_equal(out, tokens_123)
    assert expander.state.get_register(RegisterType.TOKS, "tokker")
    assert expander.get_register_value(RegisterType.TOKS, "tokker") == tokens_123
    expander.pop_scope()

    # after scope, register is back to default
    assert expander.state.get_register(RegisterType.TOKS, "tokker") == []
    assert expander.expand(r"\the\tokker") == []


def test_skips():
    expander = Expander()

    expander.expand(r"\newskip\myskip")
    expander.expand(r"\myskip=10pt plus 2pt minus 5pt")

    assert expander.get_register_value(
        RegisterType.SKIP, "myskip"
    ) == dimension_to_scaled_points(10 + 2 - 5, "pt")

    # test with dimensions as setters too
    pt_10 = dimension_to_scaled_points(10, "pt")
    expander.expand(r"\newdimen\mydimen \mydimen=10pt")
    expander.expand(r"\myskip=10pt plus 2\mydimen")
    assert expander.get_register_value(RegisterType.SKIP, "myskip") == pt_10 + 2 * pt_10

    # test with \relax
    expander.expand(r"\myskip=10pt plus 2 pt \relax minus 5 pt")
    assert expander.get_register_value(
        RegisterType.SKIP, "myskip"
    ) == dimension_to_scaled_points(10 + 2, "pt")

    # test with \def \relax
    expander.expand(r"\def\ddd{10pt plus 3 pt \relax minus 5 pt}")
    out = expander.expand(r"\myskip=\ddd")
    assert expander.get_register_value(
        RegisterType.SKIP, "myskip"
    ) == dimension_to_scaled_points(10 + 3, "pt")
    assert strip_whitespace_tokens(out) == expander.expand(r"minus 5 pt")


# def test_boxes():
#     expander = Expander()

#     # test base registers
#     expander.expand(r"\setbox0=\vbox{123}")
#     box: Box | None = expander.get_register_value(RegisterType.BOX, 0)
#     assert box is not None
#     assert box.type == "vbox"
#     assert box.content == expander.expand("123")

#     expander.expand(r"\newbox\mybox")
#     expander.expand(r"\setbox\mybox=\hbox to 10pt{abc}")
#     box: Box | None = expander.get_register_value(RegisterType.BOX, "mybox")
#     assert box is not None
#     assert box.type == "hbox"
#     assert box.content == expander.expand("abc")
