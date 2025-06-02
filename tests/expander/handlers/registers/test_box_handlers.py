from latex2json.expander.expander import Expander
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


def test_setbox():
    expander = Expander()

    # Test setting box with numeric id
    expander.expand(r"\setbox0=\vbox{123}")
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


def test_wd_ht_dp():
    expander = Expander()

    # Set up a box with dimensions
    expander.expand(r"\newbox\mybox")
    expander.expand(r"\setbox\mybox=\hbox to 10pt{abc}")
    box = expander.get_register_value(RegisterType.BOX, "mybox")
    assert isinstance(box, Box)
    box.width = 10
    box.height = 5
    box.depth = 2

    # Test dimension commands
    wd = expander.expand(r"\wd\mybox")
    assert expander.check_tokens_equal(wd, expander.expand("10"))

    ht = expander.expand(r"\ht\mybox")
    assert expander.check_tokens_equal(ht, expander.expand("5"))

    dp = expander.expand(r"\dp\mybox")
    assert expander.check_tokens_equal(dp, expander.expand("2"))
