"""Tests for expl3 dimension (dim) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestDimNew:
    """Test dim_new:N."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_new_creates_dimen(self):
        """dim_new:N should create a dimen register."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_new:N \l_my_dim
\dim_set:Nn \l_my_dim {10pt}
\dim_use:N \l_my_dim
\ExplSyntaxOff
""")
        assert to_str(result) == "10pt"


class TestDimSet:
    """Test dim_set:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_set_pt(self):
        """dim_set:Nn should set a dimension in pt."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_new:N \l_my_dim
\dim_set:Nn \l_my_dim {15pt}
\dim_use:N \l_my_dim
\ExplSyntaxOff
""")
        assert to_str(result) == "15pt"

    def test_dim_set_cm(self):
        """dim_set:Nn should handle cm units."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_new:N \l_my_dim
\dim_set:Nn \l_my_dim {1cm}
\dim_use:N \l_my_dim
\ExplSyntaxOff
""")
        assert "cm" in to_str(result) or "pt" in to_str(result)


class TestDimArithmetic:
    """Test dim arithmetic operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_zero(self):
        """dim_zero:N should reset to 0pt."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_new:N \l_my_dim
\dim_set:Nn \l_my_dim {10pt}
\dim_zero:N \l_my_dim
\dim_use:N \l_my_dim
\ExplSyntaxOff
""")
        assert to_str(result) == "0pt"


class TestDimEval:
    """Test dim_eval:n."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_eval_simple(self):
        """dim_eval:n should return a simple dimension."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_eval:n { 10pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "10pt"

    def test_dim_eval_addition(self):
        """dim_eval:n should add dimensions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_eval:n { 10pt + 5pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "15pt"

    def test_dim_eval_subtraction(self):
        """dim_eval:n should subtract dimensions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_eval:n { 20pt - 8pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "12pt"


class TestDimCompare:
    """Test dim_compare:nTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_compare_greater_true(self):
        """dim_compare:nTF with > should return true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 20pt > 10pt } {GREATER} {NOTGREATER}
\ExplSyntaxOff
""")
        assert to_str(result) == "GREATER"

    def test_dim_compare_greater_false(self):
        """dim_compare:nTF with > should return false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 5pt > 10pt } {GREATER} {NOTGREATER}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTGREATER"

    def test_dim_compare_less(self):
        """dim_compare:nTF with <."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 5pt < 10pt } {LESS} {NOTLESS}
\ExplSyntaxOff
""")
        assert to_str(result) == "LESS"

    def test_dim_compare_equal(self):
        """dim_compare:nTF with =."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 10pt = 10pt } {EQUAL} {NOTEQUAL}
\ExplSyntaxOff
""")
        assert to_str(result) == "EQUAL"

    def test_dim_compare_greater_equal(self):
        """dim_compare:nTF with >=."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 10pt >= 10pt } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_dim_compare_less_equal(self):
        """dim_compare:nTF with <=."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 5pt <= 10pt } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_dim_compare_T_variant(self):
        """dim_compare:nT only executes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\dim_compare:nT { 20pt > 10pt } {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XTRUEY"

    def test_dim_compare_F_variant(self):
        """dim_compare:nF only executes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\dim_compare:nF { 5pt > 10pt } {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XFALSEY"

    def test_dim_compare_different_units(self):
        """dim_compare:nTF should handle different units."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_compare:nTF { 1in > 2cm } {INCH_BIGGER} {CM_BIGGER}
\ExplSyntaxOff
""")
        # 1 inch = 72.27pt, 2cm = ~56.9pt, so inch is bigger
        assert to_str(result) == "INCH_BIGGER"


class TestDimMathFunctions:
    """Test dim math functions."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_abs_positive(self):
        """dim_abs:n should return positive value unchanged."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_abs:n { 10pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "10pt"

    def test_dim_abs_negative(self):
        """dim_abs:n should return absolute value of negative."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_abs:n { -15pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "15pt"

    def test_dim_sign_positive(self):
        """dim_sign:n should return 1 for positive."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_sign:n { 10pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "1"

    def test_dim_sign_negative(self):
        """dim_sign:n should return -1 for negative."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_sign:n { -10pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "-1"

    def test_dim_sign_zero(self):
        """dim_sign:n should return 0 for zero."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_sign:n { 0pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_dim_max(self):
        """dim_max:nn should return the larger dimension."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_max:nn { 10pt } { 20pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "20pt"

    def test_dim_min(self):
        """dim_min:nn should return the smaller dimension."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_min:nn { 10pt } { 20pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "10pt"


class TestDimConversion:
    """Test dim conversion functions."""

    def setup_method(self):
        self.expander = Expander()

    def test_dim_to_fp(self):
        """dim_to_fp:n should convert dimension to float."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_to_fp:n { 10pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "10"

    def test_dim_to_fp_fractional(self):
        """dim_to_fp:n should handle fractional dimensions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\dim_to_fp:n { 10.5pt }
\ExplSyntaxOff
""")
        assert to_str(result) == "10.5"
