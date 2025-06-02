from latex2json.expander.expander import Expander
from latex2json.registers import RegisterType


def test_newbool():
    expander = Expander()

    # Test creating a new boolean register
    expander.expand(r"\newbool{mybool}")
    bool_value = expander.get_register_value(RegisterType.BOOL, "mybool")
    assert bool_value is not None
    assert bool_value is False


def test_setbool():
    expander = Expander()

    # Test setting boolean values
    expander.expand(r"\newbool{testbool}")

    # Test setting to true
    expander.expand(r"\booltrue{testbool}")
    assert expander.get_register_value(RegisterType.BOOL, "testbool") is True

    # Test setting to false
    expander.expand(r"\boolfalse{testbool}")
    assert expander.get_register_value(RegisterType.BOOL, "testbool") is False


def test_ifbool():
    expander = Expander()

    # Setup test boolean
    expander.expand(r"\newbool{testbool}")

    # Test when bool is false (default)
    out = expander.expand(r"\ifbool{testbool}{TRUE}{FALSE}")
    assert out == expander.expand("FALSE")

    # Test when bool is true
    expander.expand(r"\booltrue{testbool}")
    out = expander.expand(r"\ifbool{testbool}{TRUE}{FALSE}")
    assert out == expander.expand("TRUE")

    # Test nested if statements
    expander.expand(r"\newbool{otherbool}")
    expander.expand(r"\booltrue{otherbool}")
    out = expander.expand(
        r"\ifbool{testbool}{\ifbool{otherbool}{BOTH}{FIRST}}{\ifbool{otherbool}{SECOND}{NONE}}"
    )
    assert out == expander.expand("BOTH")


def test_bool_error_cases():
    expander = Expander()

    # Test missing boolean name
    expander.expand(r"\newbool{}")  # Should not raise error but log warning

    # Test using undefined boolean
    out = expander.expand(r"\ifbool{undefinedbool}{TRUE}{FALSE}")
    assert out == expander.expand("FALSE")

    # Test incomplete ifbool blocks
    expander.expand(r"\ifbool{testbool}{TRUE}")  # Should log warning
