from latex2json.expander.expander import Expander
from latex2json.latex_maps.dimensions import dimension_to_scaled_points
from latex2json.registers import RegisterType
from latex2json.registers.types import Box


def test_newbox():
    expander = Expander()

    # Test creating a new box register
    expander.expand(r"\newbox\mybox")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert box is not None
    assert isinstance(box, Box)
    assert box.content == []

    assert expander.check_macro_is_user_defined("mybox")

    # ensure it overrides previous \def\mybox etc
    expander.expand(r"\def\myboxer{BOXER}\newbox\myboxer")
    assert expander.check_macro_is_user_defined("myboxer")
    assert expander.expand(r"\myboxer") != expander.expand("BOXER")


def test_setbox():
    expander = Expander()

    # Test setting box with numeric id
    expander.expand(r"\setbox0= \vbox{123}")
    box = expander.get_register_value(RegisterType.BOX, 0)
    assert isinstance(box, Box)
    assert box.type == "vbox"
    assert expander.check_tokens_equal(box.content, expander.expand("123"))

    # Test setting box with named register
    expander.expand(r"\newbox\mybox")
    expander.expand(r"\setbox\mybox=\hbox to 10pt{abc}")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.type == "hbox"
    assert expander.check_tokens_equal(box.content, expander.expand("abc"))

    # test that setbox immediately expands the box content
    text = r"""
    \def\aaa{AAA}
    \setbox\mybox=\vbox{\aaa} % immediately expands the box content to AAA
    \def\aaa{BBB}
""".strip()
    expander.expand(text)
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert expander.check_tokens_equal(box.content, expander.expand("AAA"))


def test_box_and_copy():
    expander = Expander()

    # Set up test boxes
    expander.expand(r"\setbox0=\vbox{123}")
    expander.expand(r"\newbox\mybox")
    expander.expand(r"\setbox\mybox=\hbox{abc}")

    # Test \copy - should preserve original box content
    copy_out = expander.expand(r"\copy0")
    assert expander.check_tokens_equal(copy_out, expander.expand("123"))
    box0 = expander.get_register_value(RegisterType.BOX, 0)
    assert isinstance(box0, Box)
    assert expander.check_tokens_equal(box0.content, expander.expand("123"))

    copy_out = expander.expand(r"\copy\mybox")
    assert expander.check_tokens_equal(copy_out, expander.expand("abc"))
    mybox = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(mybox, Box)
    assert expander.check_tokens_equal(mybox.content, expander.expand("abc"))

    # Test \box - should empty the box after use
    box_out = expander.expand(r"\box0")
    assert expander.check_tokens_equal(box_out, expander.expand("123"))
    box0 = expander.get_register_value(RegisterType.BOX, 0)
    assert isinstance(box0, Box)
    assert box0.content == []

    box_out = expander.expand(r"\box\mybox")
    assert expander.check_tokens_equal(box_out, expander.expand("abc"))
    mybox = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(mybox, Box)
    assert mybox.content == []

    # test \unvbox \unhbox
    expander.expand(r"\setbox10=\vbox{BOX 10} \setbox11=\hbox{BOX 11}")
    out = expander.expand(r"\unvbox10\unvbox10")  # 2nd one becomes empty
    assert expander.check_tokens_equal(out, expander.expand("BOX 10"))

    out = expander.expand(r"\unhbox11\unhbox11")  # 2nd one becomes empty
    assert expander.check_tokens_equal(out, expander.expand("BOX 11"))


def test_direct_hvbox_usage():
    expander = Expander()

    out = expander.expand(r"\hbox to 10pt{abc}")
    assert expander.check_tokens_equal(out, expander.expand("abc"))

    out = expander.expand(r"\vtop{abc}")
    assert expander.check_tokens_equal(out, expander.expand("abc"))


def test_box_manipulation():
    expander = Expander()

    expander.expand(r"\setbox10=\vbox{BOX 10}")
    out = expander.expand(r"\moveleft 10pt \copy10")
    assert expander.check_tokens_equal(out, expander.expand("BOX 10"))

    out = expander.expand(r"\moveright 10pt \copy10")
    assert expander.check_tokens_equal(out, expander.expand("BOX 10"))

    out = expander.expand(r"\raise 10pt \copy10")
    assert expander.check_tokens_equal(out, expander.expand("BOX 10"))

    out = expander.expand(r"\lower 10pt \copy10")
    assert expander.check_tokens_equal(out, expander.expand("BOX 10"))


def test_wd_ht_dp():
    expander = Expander()

    # Set up a box with dimensions
    expander.expand(r"\newbox\mybox")
    expander.expand(r"\setbox\mybox=\hbox to 10pt{abc}")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)

    # test assignment
    expander.expand(r"\wd \mybox=15pt")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.width == dimension_to_scaled_points(15, "pt")

    expander.expand(r"\ht\mybox =10pt")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.height == dimension_to_scaled_points(10, "pt")

    expander.expand(r"\dp\mybox = 12pt")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.depth == dimension_to_scaled_points(12, "pt")

    # test on box int id
    expander.expand(r"\setbox0=\hbox{123}")
    assert expander.expand(r"\wd0=3pt") == []
    assert expander.get_register_value(
        RegisterType.BOX, 0
    ).width == dimension_to_scaled_points(3, "pt")


def test_savebox():
    expander = Expander()

    expander.expand(r"\newsavebox\mybox")
    assert expander.check_macro_is_user_defined("mybox")

    expander.expand(r"\savebox\mybox[10pt][c]{Hello World}")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.content == expander.expand("Hello World")

    out = expander.expand(r"\usebox\mybox")
    assert expander.check_tokens_equal(out, expander.expand("Hello World"))

    # check that the box is not emptied (unlike \box)
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.content == expander.expand("Hello World")

    # \sbox{\mybox}{}  % Explicitly empty it
    expander.expand(r"\sbox{\mybox}{}")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.content == []


def test_box_commands():
    expander = Expander()

    # Test that box commands only return their text content
    test_cases = [
        (r"\makebox{Simple text}", "Simple text"),
        (r"\framebox{Simple text}", "Simple text"),
        (r"\raisebox{2pt}{Raised text}", "Raised text"),
        (r"\raisebox{2pt}[1pt][2pt]{Raised text}", "Raised text"),
        (r"\makebox[3cm]{Fixed width}", "Fixed width"),
        (r"\framebox[3cm][l]{Left in frame}", "Left in frame"),
        (r"\parbox{5cm}{Simple parbox text}", "Simple parbox text"),
        (r"\parbox[t][3cm][s]{5cm}{Stretched vertically}", "Stretched vertically"),
        (r"\fbox{Framed text}", "Framed text"),
        (r"\colorbox{yellow}{Colored box}", "Colored box"),
        (
            r"\parbox[c][3cm]{5cm}{Center aligned with fixed height}",
            "Center aligned with fixed height",
        ),
        (
            r"""\mbox{
All 
One line ajajaja
            }""",
            "All One line ajajaja",
        ),
        (r"\hbox to 3in{Some text}", "Some text"),
        (r"\pbox{3cm}{Some text}", "Some text"),
        (r"\adjustbox{max width=\textwidth}{Some text}", "Some text"),
        (r"\rotatebox{90}{Some text}", "Some text"),
    ]

    for command, expected_text in test_cases:
        out = expander.expand(command)
        assert out == expander.convert_str_to_tokens(expected_text)
