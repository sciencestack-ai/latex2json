"""
Tests for expl3 extensions covering l3int, l3cs, l3tl, l3str, l3seq,
l3keys, l3token, l3file, l3io, l3skip, and TeX primitive access handlers.
"""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestIntGincr:
    """Test int_gincr:N and int_gdecr:N handlers."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_gincr_basic(self):
        """int_gincr:N should globally increment an integer."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_new:N \g_test_int
\int_set:Nn \g_test_int {5}
\int_gincr:N \g_test_int
\int_use:N \g_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "6"

    def test_int_gdecr_basic(self):
        """int_gdecr:N should globally decrement an integer."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_new:N \g_test_int
\int_set:Nn \g_test_int {10}
\int_gdecr:N \g_test_int
\int_use:N \g_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "9"


class TestIntToAlph:
    """Test int_to_alph:n and int_to_Alph:n handlers."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_to_alph_1(self):
        """int_to_alph:n {1} should return 'a'."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_to_alph:n {1}
\ExplSyntaxOff
""")
        assert to_str(result) == "a"

    def test_int_to_alph_26(self):
        """int_to_alph:n {26} should return 'z'."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_to_alph:n {26}
\ExplSyntaxOff
""")
        assert to_str(result) == "z"

    def test_int_to_alph_27(self):
        """int_to_alph:n {27} should return 'aa'."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_to_alph:n {27}
\ExplSyntaxOff
""")
        assert to_str(result) == "aa"

    def test_int_to_Alph_1(self):
        """int_to_Alph:n {1} should return 'A'."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_to_Alph:n {1}
\ExplSyntaxOff
""")
        assert to_str(result) == "A"

    def test_int_to_roman(self):
        """int_to_roman:n {4} should return 'iv'."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_to_roman:n {4}
\ExplSyntaxOff
""")
        assert to_str(result) == "iv"

    def test_int_to_Roman(self):
        """int_to_Roman:n {4} should return 'IV'."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_to_Roman:n {4}
\ExplSyntaxOff
""")
        assert to_str(result) == "IV"


class TestCsIfFree:
    """Test cs_if_free:NTF handlers."""

    def setup_method(self):
        self.expander = Expander()

    def test_cs_if_free_undefined(self):
        """cs_if_free:NTF should take true branch for undefined command."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_if_free:NTF \undefined_cmd {FREE}{NOTFREE}
\ExplSyntaxOff
""")
        assert to_str(result) == "FREE"

    def test_cs_if_free_defined(self):
        """cs_if_free:NTF should take false branch for defined command."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\my_cmd{test}
\cs_if_free:NTF \my_cmd {FREE}{NOTFREE}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTFREE"


class TestTlIfBlank:
    """Test tl_if_blank:nTF handlers."""

    def setup_method(self):
        self.expander = Expander()

    def test_tl_if_blank_empty(self):
        """tl_if_blank:nTF should be true for empty content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_blank:nTF {} {BLANK}{NOTBLANK}
\ExplSyntaxOff
""")
        assert to_str(result) == "BLANK"

    def test_tl_if_blank_whitespace(self):
        """tl_if_blank:nTF should be true for whitespace-only content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_blank:nTF {   } {BLANK}{NOTBLANK}
\ExplSyntaxOff
""")
        assert to_str(result) == "BLANK"

    def test_tl_if_blank_content(self):
        """tl_if_blank:nTF should be false for non-blank content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_blank:nTF {text} {BLANK}{NOTBLANK}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTBLANK"


class TestStrCase:
    """Test str_case:nn handlers."""

    def setup_method(self):
        self.expander = Expander()

    def test_str_case_match(self):
        """str_case:nn should return matching case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_case:nn {two}
  {
    {one}{1}
    {two}{2}
    {three}{3}
  }
\ExplSyntaxOff
""")
        assert to_str(result) == "2"

    def test_str_case_no_match(self):
        """str_case:nn should return nothing when no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\str_case:nn {four}
  {
    {one}{1}
    {two}{2}
  }Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestSeqGputRightCn:
    """Test seq_gput_right:cn handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_gput_right_cn(self):
        """seq_gput_right:cn should append to constructed sequence name."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \g_test_seq
\seq_gput_right:cn {g_test_seq} {item1}
\seq_gput_right:cn {g_test_seq} {item2}
\seq_use:Nn \g_test_seq {-}
\ExplSyntaxOff
""")
        assert to_str(result) == "item1-item2"


class TestTexPrimitives:
    """Test tex_def:D, tex_xdef:D, tex_let:D handlers."""

    def setup_method(self):
        self.expander = Expander()

    def test_tex_def_D(self):
        """tex_def:D should push \\def primitive."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tex_def:D \test {hello}
\test
\ExplSyntaxOff
""")
        assert to_str(result) == "hello"

    def test_tex_let_D(self):
        """tex_let:D should push \\let primitive."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\original{value}
\tex_let:D \copy \original
\copy
\ExplSyntaxOff
""")
        assert to_str(result) == "value"


class TestKeysSet:
    """Test keys_set:nn handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_keys_set_consumed(self):
        """keys_set:nn should consume arguments without error."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\keys_set:nn {mymodule} {key1=value1,key2=value2}Y
\ExplSyntaxOff
""")
        # Should just consume the arguments
        assert to_str(result) == "XY"


class TestTokenToStr:
    """Test token_to_str:N handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_token_to_str_cs(self):
        """token_to_str:N should return command name without backslash."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\token_to_str:N \mycommand
\ExplSyntaxOff
""")
        assert to_str(result) == "mycommand"


class TestSkipVertical:
    """Test skip_vertical:n handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_skip_vertical_consumed(self):
        """skip_vertical:n should not produce visible output."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\skip_vertical:n {10pt}Y
\ExplSyntaxOff
""")
        # The skip is consumed by processing, leaving just X and Y
        assert "X" in to_str(result) and "Y" in to_str(result)


class TestIowNow:
    """Test iow_now:Nn handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_iow_now_consumed(self):
        """iow_now:Nn should consume arguments without producing output."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_stream_tl
X\iow_now:Nn \l_stream_tl {some content}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestJobname:
    """Test \\jobname handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_jobname_returns_document(self):
        """\\jobname should return a placeholder job name."""
        result = self.expander.expand(r"\jobname")
        assert to_str(result) == "document"


class TestCsgdef:
    """Test \\csgdef handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_csgdef_creates_command(self):
        """\\csgdef should create a globally-defined command."""
        result = self.expander.expand(r"""
\csgdef{mytest}{hello world}
\mytest
""")
        assert to_str(result) == "hello world"


class TestFileIfExist:
    """Test file_if_exist:nTF handler."""

    def setup_method(self):
        self.expander = Expander()

    def test_file_if_exist_takes_false(self):
        """file_if_exist:nTF should take false branch (we can't check files)."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\file_if_exist:nTF {somefile.tex} {EXISTS}{NOTEXISTS}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOTEXISTS"


class TestCSpaceToken:
    """Test c_space_token constant."""

    def setup_method(self):
        self.expander = Expander()

    def test_c_space_token_is_space(self):
        """c_space_token should produce a space."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\c_space_token Y
\ExplSyntaxOff
""")
        assert to_str(result) == "X Y"
