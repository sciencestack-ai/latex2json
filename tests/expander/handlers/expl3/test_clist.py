"""Tests for expl3 comma list (clist) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestClistNew:
    """Test clist_new:N and clist_clear:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_new_creates_empty_clist(self):
        """clist_new:N should create an empty comma list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_if_empty:NTF \l_my_clist {EMPTY}{NOTEMPTY}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"

    def test_clist_clear_empties_clist(self):
        """clist_clear:N should empty a comma list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {a,b,c}
\clist_clear:N \l_my_clist
\clist_if_empty:NTF \l_my_clist {EMPTY}{NOTEMPTY}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"


class TestClistSet:
    """Test clist_set:Nn and clist_gset:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_set_basic(self):
        """clist_set:Nn should set comma list content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {apple,banana,cherry}
\clist_use:Nn \l_my_clist {-}
\ExplSyntaxOff
""")
        assert to_str(result) == "apple-banana-cherry"

    def test_clist_set_overwrites(self):
        """clist_set:Nn should overwrite existing content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {old,content}
\clist_set:Nn \l_my_clist {new,data}
\clist_use:Nn \l_my_clist {-}
\ExplSyntaxOff
""")
        assert to_str(result) == "new-data"


class TestClistPut:
    """Test clist_put_right:Nn and clist_put_left:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_put_right_appends(self):
        """clist_put_right:Nn should append item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_put_right:Nn \l_my_clist {a}
\clist_put_right:Nn \l_my_clist {b}
\clist_put_right:Nn \l_my_clist {c}
\clist_use:Nn \l_my_clist {,}
\ExplSyntaxOff
""")
        assert to_str(result) == "a,b,c"

    def test_clist_put_left_prepends(self):
        """clist_put_left:Nn should prepend item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_put_left:Nn \l_my_clist {c}
\clist_put_left:Nn \l_my_clist {b}
\clist_put_left:Nn \l_my_clist {a}
\clist_use:Nn \l_my_clist {,}
\ExplSyntaxOff
""")
        assert to_str(result) == "a,b,c"

    def test_clist_put_to_empty(self):
        """clist_put_right:Nn to empty list should not add comma."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_put_right:Nn \l_my_clist {only}
\clist_count:N \l_my_clist
\ExplSyntaxOff
""")
        assert to_str(result) == "1"


class TestClistMapInline:
    """Test clist_map_inline:Nn and clist_map_inline:nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_map_inline_Nn(self):
        """clist_map_inline:Nn should iterate over items."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {x,y,z}
\clist_map_inline:Nn \l_my_clist {[#1]}
\ExplSyntaxOff
""")
        assert to_str(result) == "[x][y][z]"

    def test_clist_map_inline_nn(self):
        """clist_map_inline:nn should iterate over inline list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_map_inline:nn {a,b,c} {(#1)}
\ExplSyntaxOff
""")
        assert to_str(result) == "(a)(b)(c)"

    def test_clist_map_inline_empty(self):
        """clist_map_inline:Nn on empty list produces nothing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
X\clist_map_inline:Nn \l_my_clist {[#1]}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_clist_map_inline_with_spaces(self):
        """clist_map_inline should trim whitespace from items."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_map_inline:nn { a , b , c } {[#1]}
\ExplSyntaxOff
""")
        assert to_str(result) == "[a][b][c]"


class TestClistMapFunction:
    """Test clist_map_function:NN."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_map_function_basic(self):
        """clist_map_function:NN should apply function to each item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\wrap#1{<#1>}
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {1,2,3}
\clist_map_function:NN \l_my_clist \wrap
\ExplSyntaxOff
""")
        assert to_str(result) == "<1><2><3>"


class TestClistCount:
    """Test clist_count:N and clist_count:n."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_count_N_empty(self):
        """clist_count:N on empty list returns 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_count:N \l_my_clist
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_clist_count_N_three_items(self):
        """clist_count:N on list with three items returns 3."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {a,b,c}
\clist_count:N \l_my_clist
\ExplSyntaxOff
""")
        assert to_str(result) == "3"

    def test_clist_count_n_inline(self):
        """clist_count:n should count inline list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_count:n {one,two,three,four}
\ExplSyntaxOff
""")
        assert to_str(result) == "4"


class TestClistUse:
    """Test clist_use:Nn and clist_use:Nnnn."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_use_nn_simple(self):
        """clist_use:Nn should join with separator."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {a,b,c}
\clist_use:Nn \l_my_clist {;}
\ExplSyntaxOff
""")
        assert to_str(result) == "a;b;c"

    def test_clist_use_nnnn_two_items(self):
        """clist_use:Nnnn with two items uses sep-two."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {Alice,Bob}
\clist_use:Nnnn \l_my_clist {~and~}{,~}{,~and~}
\ExplSyntaxOff
""")
        assert to_str(result) == "Alice~and~Bob"

    def test_clist_use_nnnn_three_items(self):
        """clist_use:Nnnn with three+ items uses sep-mid and sep-last."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {A,B,C}
\clist_use:Nnnn \l_my_clist {~and~}{,~}{,~and~}
\ExplSyntaxOff
""")
        assert to_str(result) == "A,~B,~and~C"


class TestClistIfEmpty:
    """Test clist_if_empty:NTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_if_empty_true(self):
        """clist_if_empty:NTF on empty list takes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_if_empty:NTF \l_my_clist {YES}{NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_clist_if_empty_false(self):
        """clist_if_empty:NTF on non-empty list takes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {item}
\clist_if_empty:NTF \l_my_clist {YES}{NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"


class TestClistIfIn:
    """Test clist_if_in:NnTF."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_if_in_found(self):
        """clist_if_in:NnTF should find existing item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {apple,banana,cherry}
\clist_if_in:NnTF \l_my_clist {banana} {FOUND}{NOTFOUND}
\ExplSyntaxOff
""")
        assert to_str(result) == "FOUND"

    def test_clist_if_in_not_found(self):
        """clist_if_in:NnTF should not find missing item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {apple,banana,cherry}
\clist_if_in:NnTF \l_my_clist {orange} {FOUND}{NOTFOUND}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTFOUND"


class TestClistItem:
    """Test clist_item:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_item_positive_index(self):
        """clist_item:Nn with positive index (1-based)."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {first,second,third}
\clist_item:Nn \l_my_clist {2}
\ExplSyntaxOff
""")
        assert to_str(result) == "second"

    def test_clist_item_negative_index(self):
        """clist_item:Nn with negative index (from end)."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {first,second,third}
\clist_item:Nn \l_my_clist {-1}
\ExplSyntaxOff
""")
        assert to_str(result) == "third"

    def test_clist_item_first(self):
        """clist_item:Nn with index 1 gets first item."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {A,B,C}
\clist_item:Nn \l_my_clist {1}
\ExplSyntaxOff
""")
        assert to_str(result) == "A"

    def test_clist_item_out_of_range(self):
        """clist_item:Nn with out-of-range index returns nothing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {A,B}
X\clist_item:Nn \l_my_clist {5}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestClistNestedBraces:
    """Test clist handling of nested braces."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_with_braced_items(self):
        """clist should handle items with braces."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {{a,b},c,{d,e}}
\clist_count:N \l_my_clist
\ExplSyntaxOff
""")
        assert to_str(result) == "3"

    def test_clist_map_braced_items(self):
        """clist_map_inline should preserve braces in items."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\clist_set:Nn \l_my_clist {{x,y},z}
\clist_map_inline:Nn \l_my_clist {[#1]}
\ExplSyntaxOff
""")
        # The braced item should be treated as single item
        assert "[{x,y}]" in to_str(result) or "[x,y]" in to_str(result)
