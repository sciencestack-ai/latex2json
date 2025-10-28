from latex2json.expander.expander import Expander
from latex2json.registers.utils import dimension_to_scaled_points
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
    expander.expand(r"\setbox\mybox=\hbox to10pt{abc}")
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
    assert expander.convert_tokens_to_str(copy_out) == r"\vbox{123}"
    box0 = expander.get_register_value(RegisterType.BOX, 0)
    assert isinstance(box0, Box)
    assert expander.check_tokens_equal(box0.content, expander.expand("123"))

    copy_out = expander.expand(r"\copy\mybox")
    # assert expander.check_tokens_equal(copy_out, expander.expand("abc"))
    assert expander.convert_tokens_to_str(copy_out) == r"\hbox{abc}"
    mybox = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(mybox, Box)
    assert expander.check_tokens_equal(mybox.content, expander.expand("abc"))

    # Test \box - should empty the box after use
    box_out = expander.expand(r"\box0")
    assert expander.convert_tokens_to_str(box_out) == r"\vbox{123}"
    box0 = expander.get_register_value(RegisterType.BOX, 0)
    assert isinstance(box0, Box)
    assert box0.content == []

    box_out = expander.expand(r"\box\mybox")
    assert expander.convert_tokens_to_str(box_out) == r"\hbox{abc}"
    mybox = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(mybox, Box)
    assert mybox.content == []

    # test \unvbox \unhbox
    expander.expand(r"\setbox10=\vbox{BOX 10} \setbox11=\hbox{BOX 11}")
    out = expander.expand(r"\unvbox10\unvbox10")  # 2nd one becomes empty
    assert expander.convert_tokens_to_str(out) == r"\vbox{BOX 10}"

    out = expander.expand(r"\unhbox11\unhbox11")  # 2nd one becomes empty
    assert expander.convert_tokens_to_str(out) == r"\hbox{BOX 11}"


def test_direct_hvbox_usage():
    expander = Expander()

    out = expander.expand(r"\hbox to 10pt{abc}")
    assert expander.convert_tokens_to_str(out) == r"\hbox{abc}"

    out = expander.expand(r"\vtop{abc}")
    assert expander.convert_tokens_to_str(out) == r"\vtop{abc}"


def test_box_manipulation():
    expander = Expander()

    expander.expand(r"\setbox10=\vbox{BOX 10}")
    out = expander.expand(r"\moveleft 10pt \copy10")
    assert expander.convert_tokens_to_str(out) == r"\vbox{BOX 10}"

    out = expander.expand(r"\moveright 10pt \copy10")
    assert expander.convert_tokens_to_str(out) == r"\vbox{BOX 10}"

    out = expander.expand(r"\raise 10pt \copy10")
    assert expander.convert_tokens_to_str(out) == r"\vbox{BOX 10}"

    out = expander.expand(r"\lower 10pt \copy10")
    assert expander.convert_tokens_to_str(out) == r"\vbox{BOX 10}"


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
    assert expander.convert_tokens_to_str(out) == r"\hbox{Hello World}"

    # check that the box is not emptied (unlike \box)
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.content == expander.expand("Hello World")

    # \sbox{\mybox}{}  % Explicitly empty it
    expander.expand(r"\sbox{\mybox}{}")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    assert box.content == []


def test_setbox_with_bgroup_egroup():
    r"""Test \setbox with \bgroup and \egroup"""
    expander = Expander()

    # Test setbox with \bgroup...\egroup
    expander.expand(r"\setbox1=\vbox\bgroup content\egroup")
    box = expander.get_register_value(RegisterType.BOX, 1)
    assert isinstance(box, Box)
    assert box.type == "vbox"

    # Get the content as string
    content_tokens = box.content
    content_str = expander.convert_tokens_to_str(content_tokens).strip()
    assert content_str == "content"


def test_setbox_named_box_with_bgroup():
    r"""Test \setbox with named box using \bgroup"""
    expander = Expander()

    # Create a named box
    expander.expand(r"\newbox\keybox")
    expander.expand(r"\setbox\keybox=\vbox\bgroup\hsize=\textwidth content\egroup")

    # Named boxes are stored without backslash prefix
    box = expander.get_register_value(RegisterType.BOX, "keybox")
    assert isinstance(box, Box)
    assert box.type == "vbox"


def test_mixed_bgroup_and_braces():
    r"""Test that both syntaxes work equivalently"""
    expander = Expander()

    # Create two boxes with same content, different syntax
    expander.expand(r"\setbox10=\vbox{test content}")
    expander.expand(r"\setbox11=\vbox\bgroup test content\egroup")

    box1 = expander.get_register_value(RegisterType.BOX, 10)
    box2 = expander.get_register_value(RegisterType.BOX, 11)

    assert isinstance(box1, Box)
    assert isinstance(box2, Box)
    assert box1.type == box2.type

    content1 = expander.convert_tokens_to_str(box1.content).strip()
    content2 = expander.convert_tokens_to_str(box2.content).strip()
    assert content1 == content2 == "test content"


def test_nested_bgroup():
    r"""Test nested \bgroup/\egroup"""
    expander = Expander()

    expander.expand(r"\setbox20=\vbox\bgroup outer \bgroup inner\egroup\egroup")
    box = expander.get_register_value(RegisterType.BOX, 20)
    assert isinstance(box, Box)

    content_str = expander.convert_tokens_to_str(box.content).strip()
    # The inner group should be preserved
    assert "outer" in content_str
    assert "inner" in content_str
