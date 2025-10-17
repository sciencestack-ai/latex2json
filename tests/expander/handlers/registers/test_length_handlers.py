from latex2json.expander.expander import Expander
from latex2json.registers import RegisterType


def test_newlength():
    expander = Expander()

    # Test creating a new length register
    expander.expand(r"\newlength{\mylength}")
    length = expander.get_register_value(RegisterType.DIMEN, "mylength")
    assert length is not None
    assert length == 0

    # Test that the length can be referenced
    expander.expand(r"\mylength=10pt")
    assert expander.get_register_value(RegisterType.DIMEN, "mylength") > 0
    assert expander.check_macro_is_user_defined("mylength")


def test_setlength():
    expander = Expander()

    # Test setting length with basic dimension
    expander.expand(r"\newlength\testlen")
    expander.expand(r"\setlength\testlen{10pt}")
    length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    assert length is not None

    # Test setting length with expression
    expander.expand(r"\setlength{\testlen}{2em plus 1pt}")
    length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    assert length is not None

    # Test setting length with another length
    expander.expand(r"\newlength{\otherlen}")
    expander.expand(r"\setlength{\otherlen}{20pt}")
    expander.expand(r"\setlength{\testlen}{\otherlen}")
    length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    assert length == expander.get_register_value(RegisterType.DIMEN, "otherlen")


def test_addtolength():
    expander = Expander()

    # Test adding to length
    expander.expand(r"\newlength{\testlen}")
    expander.expand(r"\setlength{\testlen}{10pt}")
    initial_length = expander.get_register_value(RegisterType.DIMEN, "testlen")

    expander.expand(r"\addtolength\testlen{2\testlen}")
    new_length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    # assert new_length > initial_length

    # Test subtracting from length
    expander.expand(r"\addtolength{\testlen}{-15pt}")
    final_length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    # assert final_length < new_length

    # test it works on skips too! E.G. parskip
    expander.expand(r"\addtolength{\parskip}{15pt}")
    final_skip = expander.get_register_value(RegisterType.SKIP, "parskip")
    # assert final_skip > 0


def test_length_with_relax():
    expander = Expander()

    # Test that \relax is handled properly
    expander.expand(r"\newlength{\testlen}")
    expander.expand(r"\setlength{\testlen}{10pt\relax}")
    length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    assert length is not None

    expander.expand(r"\addtolength{\testlen}{5pt\relax}")
    new_length = expander.get_register_value(RegisterType.DIMEN, "testlen")
    assert new_length is not None


def test_ignored_length_commands():
    expander = Expander()

    # These commands should be parsed but ignored
    texts = [
        r"\newlength{\testlen}",
        r"\settowidth{\testlen}{some text}",
        r"\settoheight{\testlen}{some text}",
        r"\settodepth{\testlen}{some text}",
    ]
    for text in texts:
        out = expander.expand(text)
        assert out == []

    # Length should remain unchanged
    assert expander.get_register_value(RegisterType.DIMEN, "testlen") == 0
