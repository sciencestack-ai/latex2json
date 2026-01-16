"""Tests for expl3 floating point (fp) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestFpNew:
    """Test fp_new:N and fp_zero:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_new_creates_zero(self):
        """fp_new:N should create a variable initialized to 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_fp_zero_resets_to_zero(self):
        """fp_zero:N should reset a variable to 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_set:Nn \l_my_fp {3.14}
\fp_zero:N \l_my_fp
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "0"


class TestFpSet:
    """Test fp_set:Nn and fp_gset:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_set_simple_value(self):
        """fp_set:Nn should set a simple float value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_set:Nn \l_my_fp {3.14159}
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "3.14159"

    def test_fp_set_integer_value(self):
        """fp_set:Nn with integer should work."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_set:Nn \l_my_fp {42}
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "42"

    def test_fp_set_expression(self):
        """fp_set:Nn should evaluate expression."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_set:Nn \l_my_fp {1.5 + 2.5}
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "4"


class TestFpArithmetic:
    """Test fp_add:Nn and fp_sub:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_add_basic(self):
        """fp_add:Nn should add to current value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_set:Nn \l_my_fp {10.5}
\fp_add:Nn \l_my_fp {2.5}
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "13"

    def test_fp_sub_basic(self):
        """fp_sub:Nn should subtract from current value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_new:N \l_my_fp
\fp_set:Nn \l_my_fp {10.5}
\fp_sub:Nn \l_my_fp {2.5}
\fp_use:N \l_my_fp
\ExplSyntaxOff
""")
        assert to_str(result) == "8"


class TestFpEval:
    """Test fp_eval:n."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_eval_addition(self):
        """fp_eval:n should evaluate addition."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_eval:n {1.5 + 2.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "4"

    def test_fp_eval_multiplication(self):
        """fp_eval:n should evaluate multiplication."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_eval:n {2.5 * 4}
\ExplSyntaxOff
""")
        assert to_str(result) == "10"

    def test_fp_eval_division(self):
        """fp_eval:n should evaluate division."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_eval:n {10 / 4}
\ExplSyntaxOff
""")
        assert to_str(result) == "2.5"

    def test_fp_eval_complex_expression(self):
        """fp_eval:n should handle complex expressions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_eval:n {(1 + 2) * 3}
\ExplSyntaxOff
""")
        assert to_str(result) == "9"

    def test_fp_eval_power(self):
        """fp_eval:n should handle power (^)."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_eval:n {2 ^ 3}
\ExplSyntaxOff
""")
        assert to_str(result) == "8"


class TestFpCompare:
    """Test fp_compare:nTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_compare_greater_true(self):
        """fp_compare:nTF with greater-than, true case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {2.5 > 1.5} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_fp_compare_greater_false(self):
        """fp_compare:nTF with greater-than, false case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {1.5 > 2.5} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_fp_compare_less(self):
        """fp_compare:nTF with less-than."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {1.5 < 2.5} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_fp_compare_equal(self):
        """fp_compare:nTF with equality."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {3.14 = 3.14} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_fp_compare_not_equal(self):
        """fp_compare:nTF with inequality."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {3.14 != 2.71} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_fp_compare_greater_equal(self):
        """fp_compare:nTF with greater-or-equal."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {3.0 >= 3.0} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_fp_compare_less_equal(self):
        """fp_compare:nTF with less-or-equal."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_compare:nTF {2.5 <= 3.0} {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_fp_compare_T_variant(self):
        """fp_compare:nT only executes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\fp_compare:nT {2.5 > 1.5} {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XTRUEY"

    def test_fp_compare_F_variant(self):
        """fp_compare:nF only executes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\fp_compare:nF {1.5 > 2.5} {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XFALSEY"


class TestFpConversion:
    """Test fp_to_int:n."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_to_int_rounds(self):
        """fp_to_int:n should round to nearest integer."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_to_int:n {3.7}
\ExplSyntaxOff
""")
        assert to_str(result) == "4"

    def test_fp_to_int_rounds_down(self):
        """fp_to_int:n should round down when appropriate."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_to_int:n {3.3}
\ExplSyntaxOff
""")
        assert to_str(result) == "3"


class TestFpMathFunctions:
    """Test fp_abs:n, fp_sign:n, fp_max:nn, fp_min:nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_fp_abs_positive(self):
        """fp_abs:n of positive number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_abs:n {3.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "3.5"

    def test_fp_abs_negative(self):
        """fp_abs:n of negative number."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_abs:n {-3.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "3.5"

    def test_fp_sign_positive(self):
        """fp_sign:n of positive number returns 1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_sign:n {3.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "1"

    def test_fp_sign_negative(self):
        """fp_sign:n of negative number returns -1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_sign:n {-3.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "-1"

    def test_fp_sign_zero(self):
        """fp_sign:n of zero returns 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_sign:n {0}
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_fp_max(self):
        """fp_max:nn returns larger value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_max:nn {1.5} {2.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "2.5"

    def test_fp_min(self):
        """fp_min:nn returns smaller value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\fp_min:nn {1.5} {2.5}
\ExplSyntaxOff
""")
        assert to_str(result) == "1.5"
