"""Tests for expl3 bool handlers, including lazy boolean operators."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor
from latex2json.tokens.utils import strip_whitespace_tokens


def to_str(tokens):
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestBoolLazyAnd:
    """Test \bool_lazy_and:nnTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_bool_lazy_and_TF_takes_false_branch(self):
        r"""\bool_lazy_and:nnTF should consume all 4 args and take false branch."""
        self.expander.expand(r"\ExplSyntaxOn")
        result = self.expander.expand(
            r"\bool_lazy_and:nnTF { test1 } { test2 } { TRUE } { FALSE }"
        )
        assert to_str(result) == "FALSE"

    def test_bool_lazy_and_T_produces_nothing(self):
        r"""\bool_lazy_and:nnT should consume 3 args and produce nothing."""
        self.expander.expand(r"\ExplSyntaxOn")
        result = self.expander.expand(
            r"\bool_lazy_and:nnT { test1 } { test2 } { TRUE }"
        )
        stripped = strip_whitespace_tokens(result)
        assert len(stripped) == 0

    def test_bool_lazy_and_F_takes_false_branch(self):
        r"""\bool_lazy_and:nnF should consume 3 args and take false branch."""
        self.expander.expand(r"\ExplSyntaxOn")
        result = self.expander.expand(
            r"\bool_lazy_and:nnF { test1 } { test2 } { FALSE }"
        )
        assert to_str(result) == "FALSE"


class TestBoolLazyOr:
    """Test \bool_lazy_or:nnTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_bool_lazy_or_TF_takes_false_branch(self):
        self.expander.expand(r"\ExplSyntaxOn")
        result = self.expander.expand(
            r"\bool_lazy_or:nnTF { test1 } { test2 } { TRUE } { FALSE }"
        )
        assert to_str(result) == "FALSE"


class TestBoolLazyAndInConditional:
    """Test that expl3 bool operators work inside \\if...\\else...\\fi branches.

    This is the critical regression test: when \\ExplSyntaxOn appears inside
    a conditional branch, the tokens are pre-tokenized with wrong catcodes.
    The remerge fix should repair the split control sequences.
    """

    def setup_method(self):
        self.expander = Expander()

    def test_expl3_in_else_branch_no_infinite_loop(self):
        r"""expl3 code in \else branch should not cause infinite recursion."""
        text = r"""
\newif\ifmytest \mytestfalse
\ifmytest
    \relax
\else
    \ExplSyntaxOn
    \NewDocumentCommand \mysetcol {m m}
    {
        \bool_lazy_and:nnTF
          { \int_compare_p:nNn { \tl_count:n {#1} } = 3 }
          { \tl_if_head_eq_meaning_p:nN {#1} \mysetcol }
          { SPECIAL }
          { NORMAL:#1:#2 }
    }
    \ExplSyntaxOff
\fi
"""
        self.expander.expand(text)

        # Invoke the macro — should NOT infinite loop
        result = self.expander.expand(r"\mysetcol{A}{1}")
        result_str = to_str(result)
        assert "NORMAL" in result_str
        assert "A" in result_str

    def test_expl3_cs_remerged_in_conditional(self):
        r"""Control sequences split by wrong catcodes should be remerged."""
        text = r"""
\newif\ifmyflag \myflagfalse
\ifmyflag
    SKIP
\else
    \ExplSyntaxOn
    \cs_new:Npn \my_test_func:n #1 { RESULT:#1 }
    \ExplSyntaxOff
\fi
"""
        self.expander.expand(text)

        # The function should be registered with its full expl3 name
        from latex2json.tokens.types import Token, TokenType
        macro = self.expander.get_macro(
            Token(TokenType.CONTROL_SEQUENCE, "my_test_func:n")
        )
        assert macro is not None
