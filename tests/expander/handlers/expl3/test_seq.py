"""Tests for expl3 sequence (seq) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestSeqNew:
    """Test seq_new:N and seq_clear:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_new_creates_empty_sequence(self):
        """seq_new:N should create an empty sequence."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_if_empty:NTF \l_my_seq {EMPTY}{NOTEMPTY}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"

    def test_seq_clear_empties_sequence(self):
        """seq_clear:N should empty a sequence."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {item}
\seq_clear:N \l_my_seq
\seq_if_empty:NTF \l_my_seq {EMPTY}{NOTEMPTY}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"


class TestSeqPut:
    """Test seq_put_right:Nn and seq_put_left:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_put_right_appends_item(self):
        """seq_put_right:Nn should append an item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {a}
\seq_put_right:Nn \l_my_seq {b}
\seq_put_right:Nn \l_my_seq {c}
\seq_use:Nn \l_my_seq {,}
\ExplSyntaxOff
""")
        assert to_str(result) == "a,b,c"

    def test_seq_put_left_prepends_item(self):
        """seq_put_left:Nn should prepend an item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_left:Nn \l_my_seq {c}
\seq_put_left:Nn \l_my_seq {b}
\seq_put_left:Nn \l_my_seq {a}
\seq_use:Nn \l_my_seq {,}
\ExplSyntaxOff
""")
        assert to_str(result) == "a,b,c"

    def test_seq_put_mixed(self):
        """Mix of put_right and put_left."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {middle}
\seq_put_left:Nn \l_my_seq {first}
\seq_put_right:Nn \l_my_seq {last}
\seq_use:Nn \l_my_seq {-}
\ExplSyntaxOff
""")
        assert to_str(result) == "first-middle-last"


class TestSeqMapInline:
    """Test seq_map_inline:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_map_inline_basic(self):
        """seq_map_inline:Nn should iterate over items."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {a}
\seq_put_right:Nn \l_my_seq {b}
\seq_put_right:Nn \l_my_seq {c}
\seq_map_inline:Nn \l_my_seq {[#1]}
\ExplSyntaxOff
""")
        assert to_str(result) == "[a][b][c]"

    def test_seq_map_inline_empty_seq(self):
        """seq_map_inline:Nn on empty sequence should produce nothing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
X\seq_map_inline:Nn \l_my_seq {[#1]}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_seq_map_inline_with_commands(self):
        """seq_map_inline:Nn with commands in body."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\wrap#1{<#1>}
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {x}
\seq_put_right:Nn \l_my_seq {y}
\seq_map_inline:Nn \l_my_seq {\wrap{#1}}
\ExplSyntaxOff
""")
        assert to_str(result) == "<x><y>"


class TestSeqMapFunction:
    """Test seq_map_function:NN."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_map_function_basic(self):
        """seq_map_function:NN should apply function to each item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\process#1{(#1)}
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {1}
\seq_put_right:Nn \l_my_seq {2}
\seq_put_right:Nn \l_my_seq {3}
\seq_map_function:NN \l_my_seq \process
\ExplSyntaxOff
""")
        assert to_str(result) == "(1)(2)(3)"


class TestSeqUse:
    """Test seq_use:Nn and seq_use:Nnnn."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_use_nn_simple_separator(self):
        """seq_use:Nn should join with simple separator."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
\seq_put_right:Nn \l_my_seq {banana}
\seq_put_right:Nn \l_my_seq {cherry}
\seq_use:Nn \l_my_seq {,~}
\ExplSyntaxOff
""")
        assert to_str(result) == "apple,~banana,~cherry"

    def test_seq_use_nnnn_two_items(self):
        """seq_use:Nnnn with two items uses sep-two."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {Alice}
\seq_put_right:Nn \l_my_seq {Bob}
\seq_use:Nnnn \l_my_seq {~and~}{,~}{,~and~}
\ExplSyntaxOff
""")
        assert to_str(result) == "Alice~and~Bob"

    def test_seq_use_nnnn_three_items(self):
        """seq_use:Nnnn with three items uses sep-mid and sep-last."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {Alice}
\seq_put_right:Nn \l_my_seq {Bob}
\seq_put_right:Nn \l_my_seq {Charlie}
\seq_use:Nnnn \l_my_seq {~and~}{,~}{,~and~}
\ExplSyntaxOff
""")
        assert to_str(result) == "Alice,~Bob,~and~Charlie"

    def test_seq_use_nnnn_four_items(self):
        """seq_use:Nnnn with four items."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {A}
\seq_put_right:Nn \l_my_seq {B}
\seq_put_right:Nn \l_my_seq {C}
\seq_put_right:Nn \l_my_seq {D}
\seq_use:Nnnn \l_my_seq {~and~}{,~}{,~and~}
\ExplSyntaxOff
""")
        assert to_str(result) == "A,~B,~C,~and~D"

    def test_seq_use_one_item(self):
        """seq_use:Nnnn with one item returns just the item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {only}
\seq_use:Nnnn \l_my_seq {~and~}{,~}{,~and~}
\ExplSyntaxOff
""")
        assert to_str(result) == "only"

    def test_seq_use_empty(self):
        """seq_use:Nnnn with empty sequence returns nothing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
X\seq_use:Nnnn \l_my_seq {~and~}{,~}{,~and~}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestSeqCount:
    """Test seq_count:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_count_empty(self):
        """seq_count:N on empty sequence returns 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_count:N \l_my_seq
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_seq_count_three_items(self):
        """seq_count:N on sequence with three items returns 3."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {a}
\seq_put_right:Nn \l_my_seq {b}
\seq_put_right:Nn \l_my_seq {c}
\seq_count:N \l_my_seq
\ExplSyntaxOff
""")
        assert to_str(result) == "3"


class TestSeqIfEmpty:
    """Test seq_if_empty:NTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_if_empty_true(self):
        """seq_if_empty:NTF on empty sequence takes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_if_empty:NTF \l_my_seq {YES}{NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_seq_if_empty_false(self):
        """seq_if_empty:NTF on non-empty sequence takes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {item}
\seq_if_empty:NTF \l_my_seq {YES}{NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_seq_if_empty_T_variant(self):
        """seq_if_empty:NT only has true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
X\seq_if_empty:NT \l_my_seq {EMPTY}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XEMPTYY"

    def test_seq_if_empty_F_variant(self):
        """seq_if_empty:NF only has false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {item}
X\seq_if_empty:NF \l_my_seq {NOTEMPTY}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XNOTEMPTYY"


class TestSeqIfIn:
    """Test seq_if_in:NnTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_if_in_found(self):
        """seq_if_in:NnTF should take true branch when item exists."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
\seq_put_right:Nn \l_my_seq {banana}
\seq_if_in:NnTF \l_my_seq {apple} {FOUND} {NOT_FOUND}
\ExplSyntaxOff
""")
        assert to_str(result) == "FOUND"

    def test_seq_if_in_not_found(self):
        """seq_if_in:NnTF should take false branch when item not in seq."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
\seq_put_right:Nn \l_my_seq {banana}
\seq_if_in:NnTF \l_my_seq {orange} {FOUND} {NOT_FOUND}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOT_FOUND"

    def test_seq_if_in_T_variant(self):
        """seq_if_in:NnT only executes when item found."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
X\seq_if_in:NnT \l_my_seq {apple} {FOUND}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XFOUNDY"

    def test_seq_if_in_T_not_found(self):
        """seq_if_in:NnT does nothing when item not found."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
X\seq_if_in:NnT \l_my_seq {orange} {FOUND}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_seq_if_in_F_variant(self):
        """seq_if_in:NnF only executes when item not found."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
X\seq_if_in:NnF \l_my_seq {orange} {NOT_IN}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XNOT_INY"

    def test_seq_if_in_F_found(self):
        """seq_if_in:NnF does nothing when item found."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_put_right:Nn \l_my_seq {apple}
X\seq_if_in:NnF \l_my_seq {apple} {NOT_IN}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestSeqGetPop:
    """Test seq_get_left:NN and seq_pop_left:NN."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_get_left_retrieves_first(self):
        """seq_get_left:NN should get first item without removing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\tl_new:N \l_item_tl
\seq_put_right:Nn \l_my_seq {first}
\seq_put_right:Nn \l_my_seq {second}
\seq_get_left:NN \l_my_seq \l_item_tl
\l_item_tl-\seq_count:N \l_my_seq
\ExplSyntaxOff
""")
        assert to_str(result) == "first-2"

    def test_seq_pop_left_removes_first(self):
        """seq_pop_left:NN should get and remove first item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\tl_new:N \l_item_tl
\seq_put_right:Nn \l_my_seq {first}
\seq_put_right:Nn \l_my_seq {second}
\seq_put_right:Nn \l_my_seq {third}
\seq_pop_left:NN \l_my_seq \l_item_tl
\l_item_tl-\seq_use:Nn \l_my_seq {,}
\ExplSyntaxOff
""")
        assert to_str(result) == "first-second,third"


class TestSeqSetFromClist:
    """Test seq_set_from_clist:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_set_from_clist_basic(self):
        """seq_set_from_clist:Nn should create sequence from comma list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_set_from_clist:Nn \l_my_seq {a,b,c}
\seq_use:Nn \l_my_seq {-}
\ExplSyntaxOff
""")
        assert to_str(result) == "a-b-c"

    def test_seq_set_from_clist_with_spaces(self):
        """seq_set_from_clist:Nn should trim whitespace from items."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\seq_set_from_clist:Nn \l_my_seq {a,  b  ,c}
\seq_use:Nn \l_my_seq {|}
\ExplSyntaxOff
""")
        assert to_str(result) == "a|b|c"
