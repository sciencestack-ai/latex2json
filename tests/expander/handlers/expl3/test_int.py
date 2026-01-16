"""Tests for expl3 integer (int) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestIntBasic:
    """Test basic int operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_eval_addition(self):
        """int_eval:n should evaluate addition."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n {1 + 2}
\ExplSyntaxOff
""")
        assert to_str(result) == "3"

    def test_int_eval_multiplication(self):
        """int_eval:n should evaluate multiplication."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n {3 * 4}
\ExplSyntaxOff
""")
        assert to_str(result) == "12"

    def test_int_eval_complex(self):
        """int_eval:n should handle complex expressions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n {(2 + 3) * 4}
\ExplSyntaxOff
""")
        assert to_str(result) == "20"


class TestIntCompare:
    """Test int_compare:nTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_compare_greater_true(self):
        """int_compare:nTF with greater-than, true case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF {5 > 3} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_greater_false(self):
        """int_compare:nTF with greater-than, false case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF {3 > 5} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_int_compare_less(self):
        """int_compare:nTF with less-than."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF {3 < 5} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_equal(self):
        """int_compare:nTF with equality."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF {5 = 5} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_T_variant(self):
        """int_compare:nT only executes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\int_compare:nT {5 > 3} {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XTRUEY"

    def test_int_compare_F_variant(self):
        """int_compare:nF only executes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\int_compare:nF {3 > 5} {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XFALSEY"


class TestIntStepInline:
    """Test int_step_inline:nn and int_step_inline:nnnn."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_step_inline_nn_basic(self):
        """int_step_inline:nn should iterate from 1 to n."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_step_inline:nn {5} {[#1]}
\ExplSyntaxOff
""")
        assert to_str(result) == "[1][2][3][4][5]"

    def test_int_step_inline_nn_single(self):
        """int_step_inline:nn with n=1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_step_inline:nn {1} {#1}
\ExplSyntaxOff
""")
        assert to_str(result) == "1"

    def test_int_step_inline_nnnn_basic(self):
        """int_step_inline:nnnn with start, step, end."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_step_inline:nnnn {1} {2} {7} {#1,}
\ExplSyntaxOff
""")
        assert to_str(result) == "1,3,5,7,"

    def test_int_step_inline_nnnn_reverse(self):
        """int_step_inline:nnnn with negative step."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_step_inline:nnnn {5} {-1} {1} {#1,}
\ExplSyntaxOff
""")
        assert to_str(result) == "5,4,3,2,1,"

    def test_int_step_inline_nnnn_step_two(self):
        """int_step_inline:nnnn stepping by 2."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_step_inline:nnnn {0} {2} {8} {[#1]}
\ExplSyntaxOff
""")
        assert to_str(result) == "[0][2][4][6][8]"


class TestIntStepFunction:
    """Test int_step_function:nN and int_step_function:nnnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_step_function_nN_basic(self):
        """int_step_function:nN should call function for 1 to n."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\process#1{[#1]}
\int_step_function:nN {3} \process
\ExplSyntaxOff
""")
        assert to_str(result) == "[1][2][3]"

    def test_int_step_function_nnnN_basic(self):
        """int_step_function:nnnN with start, step, end."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\show#1{(#1)}
\int_step_function:nnnN {2} {2} {6} \show
\ExplSyntaxOff
""")
        assert to_str(result) == "(2)(4)(6)"


class TestIntCase:
    """Test int_case:nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_case_first_match(self):
        """int_case:nn should match first case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_case:nn {1} {
  {1}{ONE}
  {2}{TWO}
  {3}{THREE}
}
\ExplSyntaxOff
""")
        assert to_str(result) == "ONE"

    def test_int_case_middle_match(self):
        """int_case:nn should match middle case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_case:nn {2} {
  {1}{ONE}
  {2}{TWO}
  {3}{THREE}
}
\ExplSyntaxOff
""")
        assert to_str(result) == "TWO"

    def test_int_case_no_match(self):
        """int_case:nn with no matching case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\int_case:nn {5} {
  {1}{ONE}
  {2}{TWO}
}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestIntMathFunctions:
    """Test int_abs:n, int_sign:n, int_max:nn, int_min:nn, int_mod:nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_abs_positive(self):
        """int_abs:n of positive number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_abs:n {5}
\ExplSyntaxOff
""")
        assert to_str(result) == "5"

    def test_int_abs_negative(self):
        """int_abs:n of negative number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_abs:n {-5}
\ExplSyntaxOff
""")
        assert to_str(result) == "5"

    def test_int_sign_positive(self):
        """int_sign:n of positive number returns 1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_sign:n {10}
\ExplSyntaxOff
""")
        assert to_str(result) == "1"

    def test_int_sign_negative(self):
        """int_sign:n of negative number returns -1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_sign:n {-10}
\ExplSyntaxOff
""")
        assert to_str(result) == "-1"

    def test_int_sign_zero(self):
        """int_sign:n of zero returns 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_sign:n {0}
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_int_max(self):
        """int_max:nn returns larger value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_max:nn {3} {7}
\ExplSyntaxOff
""")
        assert to_str(result) == "7"

    def test_int_min(self):
        """int_min:nn returns smaller value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_min:nn {3} {7}
\ExplSyntaxOff
""")
        assert to_str(result) == "3"

    def test_int_mod(self):
        """int_mod:nn returns remainder."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_mod:nn {10} {3}
\ExplSyntaxOff
""")
        assert to_str(result) == "1"

    def test_int_div_truncate(self):
        """int_div_truncate:nn returns truncated division."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_div_truncate:nn {10} {3}
\ExplSyntaxOff
""")
        assert to_str(result) == "3"


class TestIntOddEven:
    """Test int_if_odd:nTF and int_if_even:nTF."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_if_odd_true(self):
        """int_if_odd:nTF with odd number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_if_odd:nTF {5} {ODD} {EVEN}
\ExplSyntaxOff
""")
        assert to_str(result) == "ODD"

    def test_int_if_odd_false(self):
        """int_if_odd:nTF with even number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_if_odd:nTF {4} {ODD} {EVEN}
\ExplSyntaxOff
""")
        assert to_str(result) == "EVEN"

    def test_int_if_even_true(self):
        """int_if_even:nTF with even number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_if_even:nTF {4} {EVEN} {ODD}
\ExplSyntaxOff
""")
        assert to_str(result) == "EVEN"

    def test_int_if_even_false(self):
        """int_if_even:nTF with odd number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_if_even:nTF {5} {EVEN} {ODD}
\ExplSyntaxOff
""")
        assert to_str(result) == "ODD"

    def test_int_if_odd_zero(self):
        """int_if_odd:nTF with zero (even)."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_if_odd:nTF {0} {ODD} {EVEN}
\ExplSyntaxOff
""")
        assert to_str(result) == "EVEN"
