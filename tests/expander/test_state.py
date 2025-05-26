import pytest

from latex2json.expander.macro_registry import Macro
from latex2json.registers import RegisterType
from latex2json.expander.state import ExpanderState, StateLayer, ProcessingMode
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.tokenizer import Tokenizer


def test_state_scopes():
    tokenizer = Tokenizer()

    state = ExpanderState(tokenizer)

    # test macro scopes
    def test_macro_scopes():
        test_macro = Macro("testxx", lambda expander, node: [])

        assert not state.get_macro("test")

        state.push_scope()
        state.set_macro("test", test_macro)
        assert state.get_macro("test")

        state.push_scope()
        assert state.get_macro("test")
        state.set_macro("test2", test_macro)
        assert state.get_macro("test2")

        state.pop_scope()
        assert state.get_macro("test")
        assert not state.get_macro("test2")

        state.pop_scope()
        assert not state.get_macro("test")

    def test_catcode_scopes():
        # default other
        assert state.get_catcode(ord("a")) == Catcode.LETTER

        state.push_scope()

        # test catcodes
        state.set_catcode(ord("a"), Catcode.IGNORED)
        assert state.get_catcode(ord("a")) == Catcode.IGNORED
        assert tokenizer.get_catcode(ord("a")) == Catcode.IGNORED

        state.push_scope()
        # catcode should be unchanged in the new scope
        assert state.get_catcode(ord("a")) == Catcode.IGNORED
        assert tokenizer.get_catcode(ord("a")) == Catcode.IGNORED

        state.pop_scope()
        # same
        assert state.get_catcode(ord("a")) == Catcode.IGNORED
        assert tokenizer.get_catcode(ord("a")) == Catcode.IGNORED

        # back to default
        state.pop_scope()
        assert state.get_catcode(ord("a")) == Catcode.LETTER

    def test_mode_scopes():
        # test modes
        state.set_mode(ProcessingMode.MATH)
        assert state.mode == ProcessingMode.MATH

        state.push_scope()
        assert state.mode == ProcessingMode.MATH

        state.pop_scope()
        assert state.mode == ProcessingMode.MATH

    def test_register_scopes():
        # test registers
        reg_type = RegisterType.COUNT
        state.set_register(reg_type, 0, 10)
        assert state.get_register(reg_type, 0) == 10

        state.push_scope()
        assert state.get_register(reg_type, 0) == 10

        # set to 20
        state.set_register(reg_type, 0, 20)
        assert state.get_register(reg_type, 0) == 20
        state.set_register(reg_type, 0, 30)
        assert state.get_register(reg_type, 0) == 30

        # set \count1 to 30
        state.set_register(reg_type, 1, 30)
        assert state.get_register(reg_type, 1) == 30

        state.pop_scope()
        assert state.get_register(reg_type, 0) == 10  # original pre-scope
        assert state.get_register(reg_type, 1) == 0  # default to 0

        # test global
        state.push_scope()
        state.set_register(reg_type, 0, 100, is_global=True)
        assert state.get_register(reg_type, 0) == 100
        state.pop_scope()
        assert state.get_register(reg_type, 0) == 100

    test_macro_scopes()
    test_catcode_scopes()
    test_mode_scopes()
    test_register_scopes()


def test_math_mode_catcodes():
    tokenizer = Tokenizer()
    state = ExpanderState(tokenizer)

    # Check initial catcodes
    assert state.get_catcode(ord("_")) == Catcode.SUBSCRIPT
    assert state.get_catcode(ord("^")) == Catcode.SUPERSCRIPT
    assert state.get_catcode(ord("&")) == Catcode.ALIGNMENT_TAB

    # Enter math mode
    state.set_mode(ProcessingMode.MATH)

    # Check math mode catcodes
    assert state.get_catcode(ord("_")) == Catcode.ACTIVE
    assert state.get_catcode(ord("^")) == Catcode.ACTIVE
    assert state.get_catcode(ord("&")) == Catcode.ACTIVE

    # Exit math mode
    state.set_mode(ProcessingMode.TEXT)

    # Check catcodes are restored
    assert state.get_catcode(ord("_")) == Catcode.SUBSCRIPT
    assert state.get_catcode(ord("^")) == Catcode.SUPERSCRIPT
    assert state.get_catcode(ord("&")) == Catcode.ALIGNMENT_TAB

    # Test nested scopes with math mode
    state.set_catcode(ord("_"), 5)
    state.push_scope()
    state.set_mode(ProcessingMode.MATH)
    assert state.get_catcode(ord("_")) == Catcode.ACTIVE

    state.set_mode(ProcessingMode.TEXT)
    state.pop_scope()
    assert state.get_catcode(ord("_")) == 5
