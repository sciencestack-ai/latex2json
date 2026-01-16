"""Tests for expl3 property list (prop) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestPropNew:
    """Test prop_new:N and prop_clear:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_new_creates_empty_prop(self):
        """prop_new:N should create an empty property list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_if_empty:NTF \l_my_prop {EMPTY}{NOTEMPTY}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"


class TestPropPut:
    """Test prop_put:Nnn."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_put_adds_key(self):
        """prop_put:Nnn should add key-value pair."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {name} {Alice}
\prop_item:Nn \l_my_prop {name}
\ExplSyntaxOff
""")
        assert to_str(result) == "Alice"

    def test_prop_put_updates_key(self):
        """prop_put:Nnn should update existing key."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {name} {Alice}
\prop_put:Nnn \l_my_prop {name} {Bob}
\prop_item:Nn \l_my_prop {name}
\ExplSyntaxOff
""")
        assert to_str(result) == "Bob"

    def test_prop_put_multiple_keys(self):
        """prop_put:Nnn should handle multiple keys."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {a} {1}
\prop_put:Nnn \l_my_prop {b} {2}
\prop_put:Nnn \l_my_prop {c} {3}
\prop_item:Nn \l_my_prop {a}-\prop_item:Nn \l_my_prop {b}-\prop_item:Nn \l_my_prop {c}
\ExplSyntaxOff
""")
        assert to_str(result) == "1-2-3"


class TestPropGet:
    """Test prop_get:NnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_get_retrieves_value(self):
        """prop_get:NnN should retrieve value into variable."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\tl_new:N \l_result_tl
\prop_put:Nnn \l_my_prop {key} {value}
\prop_get:NnN \l_my_prop {key} \l_result_tl
\l_result_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "value"


class TestPropIfIn:
    """Test prop_if_in:NnTF."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_if_in_found(self):
        """prop_if_in:NnTF should find existing key."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {mykey} {myval}
\prop_if_in:NnTF \l_my_prop {mykey} {FOUND}{NOTFOUND}
\ExplSyntaxOff
""")
        assert to_str(result) == "FOUND"

    def test_prop_if_in_not_found(self):
        """prop_if_in:NnTF should not find missing key."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {mykey} {myval}
\prop_if_in:NnTF \l_my_prop {otherkey} {FOUND}{NOTFOUND}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTFOUND"


class TestPropCount:
    """Test prop_count:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_count_empty(self):
        """prop_count:N on empty prop returns 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_count:N \l_my_prop
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_prop_count_three_items(self):
        """prop_count:N on prop with three items returns 3."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {a} {1}
\prop_put:Nnn \l_my_prop {b} {2}
\prop_put:Nnn \l_my_prop {c} {3}
\prop_count:N \l_my_prop
\ExplSyntaxOff
""")
        assert to_str(result) == "3"


class TestPropMapInline:
    """Test prop_map_inline:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_map_inline_basic(self):
        """prop_map_inline:Nn should iterate over key-value pairs."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {a} {1}
\prop_put:Nnn \l_my_prop {b} {2}
\prop_map_inline:Nn \l_my_prop {[#1=#2]}
\ExplSyntaxOff
""")
        assert to_str(result) == "[a=1][b=2]"


class TestPropRemove:
    """Test prop_remove:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_remove_removes_key(self):
        """prop_remove:Nn should remove key from prop."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_put:Nnn \l_my_prop {a} {1}
\prop_put:Nnn \l_my_prop {b} {2}
\prop_remove:Nn \l_my_prop {a}
\prop_count:N \l_my_prop
\ExplSyntaxOff
""")
        assert to_str(result) == "1"


class TestPropSetFromKeyval:
    """Test prop_set_from_keyval:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_prop_set_from_keyval_basic(self):
        """prop_set_from_keyval:Nn should parse key=value format."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\prop_new:N \l_my_prop
\prop_set_from_keyval:Nn \l_my_prop {name=Alice,age=30}
\prop_item:Nn \l_my_prop {name}-\prop_item:Nn \l_my_prop {age}
\ExplSyntaxOff
""")
        assert to_str(result) == "Alice-30"
