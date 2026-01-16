"""Tests for expl3 (LaTeX3) syntax handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor
from latex2json.tokens.catcodes import Catcode


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestExplSyntaxOnOff:
    """Test ExplSyntaxOn and ExplSyntaxOff catcode changes."""

    def setup_method(self):
        self.expander = Expander()

    def test_expl_syntax_on_changes_underscore_catcode(self):
        """Underscore should become LETTER in expl3 mode."""
        assert self.expander.get_catcode(ord("_")) == Catcode.SUBSCRIPT
        self.expander.expand(r"\ExplSyntaxOn")
        assert self.expander.get_catcode(ord("_")) == Catcode.LETTER

    def test_expl_syntax_on_changes_colon_catcode(self):
        """Colon should become LETTER in expl3 mode."""
        assert self.expander.get_catcode(ord(":")) == Catcode.OTHER
        self.expander.expand(r"\ExplSyntaxOn")
        assert self.expander.get_catcode(ord(":")) == Catcode.LETTER

    def test_expl_syntax_on_ignores_spaces(self):
        """Spaces should be IGNORED in expl3 mode."""
        assert self.expander.get_catcode(ord(" ")) == Catcode.SPACE
        self.expander.expand(r"\ExplSyntaxOn")
        assert self.expander.get_catcode(ord(" ")) == Catcode.IGNORED

    def test_expl_syntax_off_restores_catcodes(self):
        """ExplSyntaxOff should restore default catcodes."""
        self.expander.expand(r"\ExplSyntaxOn")
        self.expander.expand(r"\ExplSyntaxOff")
        assert self.expander.get_catcode(ord("_")) == Catcode.SUBSCRIPT
        assert self.expander.get_catcode(ord(":")) == Catcode.OTHER
        assert self.expander.get_catcode(ord(" ")) == Catcode.SPACE

    def test_expl3_command_tokenization(self):
        """Commands with _ and : should tokenize as single control sequence."""
        self.expander.expand(r"\ExplSyntaxOn")
        self.expander.set_text(r"\cs_new_eq:NN")
        tok = self.expander.consume()
        assert tok.value == "cs_new_eq:NN"


class TestCsNewEq:
    """Test cs_new_eq:NN and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_cs_new_eq_creates_alias(self):
        """cs_new_eq:NN should create an alias like let."""
        self.expander.expand(r"\def\original#1{HELLO #1}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_new_eq:NN \myalias \original
\myalias{world}
\ExplSyntaxOff
""")
        assert to_str(result) == "HELLO world"

    def test_cs_set_eq_creates_alias(self):
        """cs_set_eq:NN should also create an alias."""
        self.expander.expand(r"\def\foo{FOO}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_set_eq:NN \bar \foo
\bar
\ExplSyntaxOff
""")
        assert to_str(result) == "FOO"


class TestCsNewNpn:
    """Test cs_new:Npn and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_cs_new_npn_defines_command(self):
        """cs_new:Npn should define a command like def."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_new:Npn \greet #1 {Hello,#1!}
\greet{World}
\ExplSyntaxOff
""")
        assert to_str(result) == "Hello,World!"

    def test_cs_new_npn_with_multiple_args(self):
        """cs_new:Npn should handle multiple arguments."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_new:Npn \pair #1#2 {(#1,#2)}
\pair{a}{b}
\ExplSyntaxOff
""")
        assert to_str(result) == "(a,b)"


class TestStrCase:
    """Test str_case:nnF string pattern matching."""

    def setup_method(self):
        self.expander = Expander()

    def test_str_case_matches_first(self):
        """str_case:nnF should match first case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_case:nnF {red}{
  {red}{RED}
  {blue}{BLUE}
}{UNKNOWN}
\ExplSyntaxOff
""")
        assert to_str(result) == "RED"

    def test_str_case_matches_second(self):
        """str_case:nnF should match second case."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_case:nnF {blue}{
  {red}{RED}
  {blue}{BLUE}
}{UNKNOWN}
\ExplSyntaxOff
""")
        assert to_str(result) == "BLUE"

    def test_str_case_fallback(self):
        """str_case:nnF should use fallback when no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_case:nnF {green}{
  {red}{RED}
  {blue}{BLUE}
}{FALLBACK}
\ExplSyntaxOff
""")
        assert to_str(result) == "FALLBACK"

    def test_str_case_empty_test(self):
        """str_case:nnF should handle empty test string."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_case:nnF {}{
  {}{EMPTY}
  {x}{X}
}{FALLBACK}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"


class TestUseCommands:
    """Test use:n and use_none:n."""

    def setup_method(self):
        self.expander = Expander()

    def test_use_n_returns_content(self):
        """use:n should return its argument unchanged."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\use:n {hello}
\ExplSyntaxOff
""")
        assert to_str(result) == "hello"

    def test_use_none_discards_content(self):
        """use_none:n should discard its argument."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
before\use_none:n {DISCARDED}after
\ExplSyntaxOff
""")
        assert to_str(result) == "beforeafter"


class TestProvidesExpl:
    """Test ProvidesExplPackage and ProvidesExplClass."""

    def setup_method(self):
        self.expander = Expander()

    def test_provides_expl_package_enables_syntax(self):
        """ProvidesExplPackage should enable expl3 syntax."""
        self.expander.expand(r"\ProvidesExplPackage{test}{2024/01/01}{1.0}{Test}")
        assert self.expander.get_catcode(ord("_")) == Catcode.LETTER
        assert self.expander.get_catcode(ord(":")) == Catcode.LETTER


class TestExpArgs:
    """Test exp_args expansion control."""

    def setup_method(self):
        self.expander = Expander()

    def test_exp_args_Nx_expands_arg(self):
        """exp_args:Nx should fully expand the argument."""
        self.expander.expand(r"\def\myval{EXPANDED}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\exp_args:Nx \use:n {\myval}
\ExplSyntaxOff
""")
        assert to_str(result) == "EXPANDED"

    def test_exp_args_NV_gets_variable_value(self):
        """exp_args:NV should get the value of a variable."""
        self.expander.expand(r"\def\myvar{VARVALUE}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\exp_args:NV \use:n \myvar
\ExplSyntaxOff
""")
        assert to_str(result) == "VARVALUE"

    def test_exp_args_Nc_constructs_csname(self):
        """exp_args:Nc should construct a control sequence from name."""
        self.expander.expand(r"\def\foo{FOO}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\exp_args:Nc \use:n {foo}
\ExplSyntaxOff
""")
        assert to_str(result) == "FOO"


class TestTlVariables:
    """Test token list variable operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_tl_new_creates_empty_variable(self):
        """tl_new:N should create an empty token list variable."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
X\l_my_tl Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_tl_set_assigns_value(self):
        """tl_set:Nn should assign a value to a token list variable."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {hello}
\l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "hello"

    def test_tl_gset_assigns_globally(self):
        """tl_gset:Nn should assign a value globally."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \g_my_tl
{
  \tl_gset:Nn \g_my_tl {global~value}
}
\g_my_tl
\ExplSyntaxOff
""")
        assert "global" in to_str(result)

    def test_tl_use_expands_variable(self):
        """tl_use:N should expand the token list variable."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {content}
\tl_use:N \l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "content"

    def test_tl_put_right_appends(self):
        """tl_put_right:Nn should append to existing content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {hello}
\tl_put_right:Nn \l_my_tl {~world}
\l_my_tl
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "hello" in out and "world" in out


class TestStrIfEq:
    """Test string equality conditionals."""

    def setup_method(self):
        self.expander = Expander()

    def test_str_if_eq_TF_true(self):
        """str_if_eq:nnTF should execute true branch on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_if_eq:nnTF {abc} {abc} {EQUAL} {NOT}
\ExplSyntaxOff
""")
        assert to_str(result) == "EQUAL"

    def test_str_if_eq_TF_false(self):
        """str_if_eq:nnTF should execute false branch on mismatch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\str_if_eq:nnTF {abc} {xyz} {EQUAL} {NOT}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOT"

    def test_str_if_eq_T_match(self):
        """str_if_eq:nnT should execute branch on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\str_if_eq:nnT {a} {a} {YES}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XYESY"

    def test_str_if_eq_T_no_match(self):
        """str_if_eq:nnT should do nothing on mismatch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\str_if_eq:nnT {a} {b} {YES}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_str_if_eq_F_match(self):
        """str_if_eq:nnF should do nothing on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\str_if_eq:nnF {a} {a} {NO}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_str_if_eq_F_no_match(self):
        """str_if_eq:nnF should execute branch on mismatch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\str_if_eq:nnF {a} {b} {NO}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XNOY"


class TestTlIfEmpty:
    """Test token list empty conditionals."""

    def setup_method(self):
        self.expander = Expander()

    def test_tl_if_empty_TF_empty(self):
        """tl_if_empty:nTF should execute true branch when empty."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_empty:nTF {} {EMPTY} {NOT}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"

    def test_tl_if_empty_TF_not_empty(self):
        """tl_if_empty:nTF should execute false branch when not empty."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_empty:nTF {x} {EMPTY} {NOT}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOT"

    def test_tl_if_empty_T_empty(self):
        """tl_if_empty:nT should execute branch when empty."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\tl_if_empty:nT {} {EMPTY}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XEMPTYY"

    def test_tl_if_empty_F_not_empty(self):
        """tl_if_empty:nF should execute branch when not empty."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\tl_if_empty:nF {content} {NOTEMPTY}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XNOTEMPTYY"


class TestIntCompare:
    """Test integer comparison conditionals."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_compare_greater_true(self):
        """int_compare:nTF should handle > correctly."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF { 5 > 3 } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_greater_false(self):
        """int_compare:nTF should handle > correctly when false."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF { 2 > 3 } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_int_compare_less(self):
        """int_compare:nTF should handle < correctly."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF { 1 < 5 } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_equal(self):
        """int_compare:nTF should handle = correctly."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF { 3 = 3 } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_not_equal(self):
        """int_compare:nTF should handle != correctly."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF { 3 != 5 } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_int_compare_greater_equal(self):
        """int_compare:nTF should handle >= correctly."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_compare:nTF { 5 >= 5 } {YES} {NO}
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"


class TestIntEval:
    """Test integer evaluation."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_eval_addition(self):
        """int_eval:n should handle addition."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n { 2 + 3 }
\ExplSyntaxOff
""")
        assert to_str(result) == "5"

    def test_int_eval_multiplication(self):
        """int_eval:n should handle multiplication."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n { 4 * 5 }
\ExplSyntaxOff
""")
        assert to_str(result) == "20"

    def test_int_eval_complex(self):
        """int_eval:n should handle complex expressions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n { 2 + 3 * 4 }
\ExplSyntaxOff
""")
        assert to_str(result) == "14"

    def test_int_eval_parentheses(self):
        """int_eval:n should respect parentheses."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n { (2 + 3) * 4 }
\ExplSyntaxOff
""")
        assert to_str(result) == "20"

    def test_int_eval_subtraction(self):
        """int_eval:n should handle subtraction."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n { 10 - 3 }
\ExplSyntaxOff
""")
        assert to_str(result) == "7"

    def test_int_eval_division(self):
        """int_eval:n should handle division (integer)."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_eval:n { 10 / 3 }
\ExplSyntaxOff
""")
        assert to_str(result) == "3"


class TestExpNot:
    """Test expansion prevention commands."""

    def setup_method(self):
        self.expander = Expander()

    def test_exp_not_n_prevents_expansion(self):
        """exp_not:n should return tokens without expanding."""
        self.expander.expand(r"\def\foo{EXPANDED}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\exp_not:n {\foo}
\ExplSyntaxOff
""")
        # The \foo should not be expanded
        out = to_str(result)
        assert "EXPANDED" not in out or "foo" in out

    def test_exp_not_N_prevents_expansion(self):
        """exp_not:N should return single token without expanding."""
        self.expander.expand(r"\def\foo{EXPANDED}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\exp_not:N \foo
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "EXPANDED" not in out or "foo" in out

    def test_exp_not_c_constructs_unexpanded(self):
        """exp_not:c should construct control sequence without expanding."""
        self.expander.expand(r"\def\mycs{EXPANDED}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\exp_not:c {mycs}
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "EXPANDED" not in out or "mycs" in out


class TestCsIfExist:
    """Test control sequence existence conditionals."""

    def setup_method(self):
        self.expander = Expander()

    def test_cs_if_exist_TF_exists(self):
        """cs_if_exist:NTF should execute true branch when command exists."""
        self.expander.expand(r"\def\mycommand{value}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_if_exist:NTF \mycommand {EXISTS} {MISSING}
\ExplSyntaxOff
""")
        assert to_str(result) == "EXISTS"

    def test_cs_if_exist_TF_missing(self):
        """cs_if_exist:NTF should execute false branch when command missing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_if_exist:NTF \undefinedcmd {EXISTS} {MISSING}
\ExplSyntaxOff
""")
        assert to_str(result) == "MISSING"

    def test_cs_if_exist_T_exists(self):
        """cs_if_exist:NT should execute branch when command exists."""
        self.expander.expand(r"\def\mycommand{value}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\cs_if_exist:NT \mycommand {EXISTS}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XEXISTSY"

    def test_cs_if_exist_T_missing(self):
        """cs_if_exist:NT should do nothing when command missing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\cs_if_exist:NT \undefinedcmd {EXISTS}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_cs_if_exist_F_exists(self):
        """cs_if_exist:NF should do nothing when command exists."""
        self.expander.expand(r"\def\mycommand{value}")
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\cs_if_exist:NF \mycommand {MISSING}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_cs_if_exist_F_missing(self):
        """cs_if_exist:NF should execute branch when command missing."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\cs_if_exist:NF \undefinedcmd {MISSING}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XMISSINGY"


class TestCsToStr:
    """Test control sequence to string conversion."""

    def setup_method(self):
        self.expander = Expander()

    def test_cs_to_str_basic(self):
        """cs_to_str:N should return command name without backslash."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_to_str:N \mycommand
\ExplSyntaxOff
""")
        assert to_str(result) == "mycommand"

    def test_cs_to_str_expl3_name(self):
        """cs_to_str:N should work with expl3-style names."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\cs_to_str:N \my_command:nn
\ExplSyntaxOff
""")
        assert to_str(result) == "my_command:nn"


class TestCsGenerateVariant:
    """Test cs_generate_variant:Nn (mostly a no-op)."""

    def setup_method(self):
        self.expander = Expander()

    def test_cs_generate_variant_consumes_args(self):
        """cs_generate_variant:Nn should consume arguments without error."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\cs_generate_variant:Nn \some_func:nn {Vn,xn}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestGrouping:
    """Test group_begin: and group_end:."""

    def setup_method(self):
        self.expander = Expander()

    def test_group_begin_end_scoping(self):
        """group_begin: and group_end: should provide proper scoping."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\x{outer}
\group_begin:
  \def\x{inner}
  \x
\group_end:
\x
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "inner" in out and "outer" in out


class TestIntVariables:
    """Test integer variable operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_int_set_and_use(self):
        """int_set:Nn and int_use:N should work together."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\newcount\l_test_int
\int_set:Nn \l_test_int {42}
\int_use:N \l_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "42"

    def test_int_zero(self):
        """int_zero:N should set integer to zero."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\newcount\l_test_int
\l_test_int=99
\int_zero:N \l_test_int
\int_use:N \l_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_int_incr(self):
        """int_incr:N should increment integer by 1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\newcount\l_test_int
\int_set:Nn \l_test_int {5}
\int_incr:N \l_test_int
\int_use:N \l_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "6"

    def test_int_decr(self):
        """int_decr:N should decrement integer by 1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\newcount\l_test_int
\int_set:Nn \l_test_int {10}
\int_decr:N \l_test_int
\int_use:N \l_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "9"

    def test_int_add(self):
        """int_add:Nn should add to integer."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\newcount\l_test_int
\int_set:Nn \l_test_int {10}
\int_add:Nn \l_test_int {5}
\int_use:N \l_test_int
\ExplSyntaxOff
""")
        assert to_str(result) == "15"


class TestMoreTlFunctions:
    """Test additional token list functions."""

    def setup_method(self):
        self.expander = Expander()

    def test_tl_put_left_prepends(self):
        """tl_put_left:Nn should prepend to existing content."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {world}
\tl_put_left:Nn \l_my_tl {hello~}
\l_my_tl
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "hello" in out and "world" in out
        # hello should come before world
        assert out.index("hello") < out.index("world")

    def test_tl_clear_empties_variable(self):
        """tl_clear:N should empty the token list variable."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {content}
\tl_clear:N \l_my_tl
X\l_my_tl Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_tl_to_str_n(self):
        """tl_to_str:n should convert tokens to string."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_to_str:n {hello}
\ExplSyntaxOff
""")
        assert to_str(result) == "hello"

    def test_tl_if_eq_TF_equal(self):
        """tl_if_eq:nnTF should execute true branch when equal."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_eq:nnTF {abc} {abc} {EQUAL} {NOT}
\ExplSyntaxOff
""")
        assert to_str(result) == "EQUAL"

    def test_tl_if_eq_TF_not_equal(self):
        """tl_if_eq:nnTF should execute false branch when not equal."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_if_eq:nnTF {abc} {xyz} {EQUAL} {NOT}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOT"

    def test_tl_head_gets_first(self):
        """tl_head:n should return first token."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_head:n {abc}
\ExplSyntaxOff
""")
        assert to_str(result) == "a"

    def test_tl_tail_gets_rest(self):
        """tl_tail:n should return all but first token."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_tail:n {abcd}
\ExplSyntaxOff
""")
        assert to_str(result) == "bcd"

    def test_tl_range_first_char(self):
        """tl_range:nnn should extract first character."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_range:nnn {Dflg} {1} {1}
\ExplSyntaxOff
""")
        assert to_str(result) == "D"

    def test_tl_range_from_second_to_end(self):
        """tl_range:nnn should extract from position to end with -1."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_range:nnn {Dflg} {2} {-1}
\ExplSyntaxOff
""")
        assert to_str(result) == "flg"

    def test_tl_range_middle(self):
        """tl_range:nnn should extract middle portion."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_range:nnn {abcde} {2} {4}
\ExplSyntaxOff
""")
        assert to_str(result) == "bcd"

    def test_tl_range_negative_indices(self):
        """tl_range:nnn should handle negative indices."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_range:nnn {abcde} {-2} {-1}
\ExplSyntaxOff
""")
        assert to_str(result) == "de"

    def test_tl_range_in_macro(self):
        """tl_range:nnn should work inside macro definitions."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\newcommand{\cat}[1]{
  \mathcal{\tl_range:nnn {#1} {1} {1}}~
  \text{\tl_range:nnn {#1} {2} {-1}}
}
\ExplSyntaxOff
\cat{Dflg}
""")
        out = to_str(result)
        assert "\\mathcal{D}" in out
        assert "\\text{flg}" in out


class TestPrgFunctions:
    """Test programming utility functions."""

    def setup_method(self):
        self.expander = Expander()

    def test_prg_do_nothing(self):
        """prg_do_nothing: should expand to nothing."""
        # Use ~ as separator in expl3 mode, otherwise Y attaches to command name
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\prg_do_nothing:~Y
\ExplSyntaxOff
""")
        # The ~ produces a space-like token but may be rendered as ~ or space
        out = to_str(result)
        assert "X" in out and "Y" in out and "prg" not in out

    def test_prg_return_true(self):
        """prg_return_true: should expand without error."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\prg_return_true:~Y
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "X" in out and "Y" in out and "prg" not in out

    def test_prg_return_false(self):
        """prg_return_false: should expand without error."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\prg_return_false:~Y
\ExplSyntaxOff
""")
        out = to_str(result)
        assert "X" in out and "Y" in out and "prg" not in out


class TestBoolFunctions:
    """Test boolean operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_bool_new_creates_false(self):
        """bool_new:N should create a false boolean."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\bool_new:N \l_my_bool
\bool_if:NTF \l_my_bool {TRUE} {FALSE}
\ExplSyntaxOff
""")
        assert to_str(result) == "FALSE"

    def test_bool_set_true(self):
        """bool_set_true:N should set boolean to true."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\bool_new:N \l_my_bool
\bool_set_true:N \l_my_bool
\bool_if:NTF \l_my_bool {TRUE} {FALSE}
\ExplSyntaxOff
""")
        assert to_str(result) == "TRUE"

    def test_bool_set_false(self):
        """bool_set_false:N should set boolean to false."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\bool_new:N \l_my_bool
\bool_set_true:N \l_my_bool
\bool_set_false:N \l_my_bool
\bool_if:NTF \l_my_bool {TRUE} {FALSE}
\ExplSyntaxOff
""")
        assert to_str(result) == "FALSE"


class TestSeqFunctions:
    """Test sequence operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_seq_new_creates_empty(self):
        """seq_new:N should create an empty sequence."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
X\l_my_seq Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_seq_clear_empties(self):
        """seq_clear:N should empty the sequence."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_my_seq
\def\l_my_seq{content}
\seq_clear:N \l_my_seq
X\l_my_seq Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestClistFunctions:
    """Test comma list operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_clist_new_creates_empty(self):
        """clist_new:N should create an empty comma list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
X\l_my_clist Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_clist_clear_empties(self):
        """clist_clear:N should empty the comma list."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\clist_new:N \l_my_clist
\def\l_my_clist{a,b,c}
\clist_clear:N \l_my_clist
X\l_my_clist Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"


class TestQuarkFunctions:
    """Test quark special value operations."""

    def setup_method(self):
        self.expander = Expander()

    def test_quark_if_no_value_true(self):
        """quark_if_no_value:NTF should detect q_no_value."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\quark_if_no_value:NTF \q_no_value {NOVALUE} {HASVALUE}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOVALUE"

    def test_quark_if_no_value_false(self):
        """quark_if_no_value:NTF should detect regular tokens."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\def\mytoken{x}
\quark_if_no_value:NTF \mytoken {NOVALUE} {HASVALUE}
\ExplSyntaxOff
""")
        assert to_str(result) == "HASVALUE"
