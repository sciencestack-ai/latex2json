"""Tests for expl3 tl (token list) handlers."""

from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor
from latex2json.tokens.utils import strip_whitespace_tokens


def to_str(tokens):
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestTlCount:
    r"""Test \tl_count:n."""

    def setup_method(self):
        self.expander = Expander()
        self.expander.expand(r"\ExplSyntaxOn")

    def test_count_simple_tokens(self):
        result = self.expander.expand(r"\tl_count:n { a b c }")
        assert to_str(result) == "3"

    def test_count_brace_group_as_one(self):
        r"""A brace group {xyz} counts as a single item."""
        result = self.expander.expand(r"\tl_count:n { a {bc} d }")
        assert to_str(result) == "3"

    def test_count_empty(self):
        result = self.expander.expand(r"\tl_count:n { }")
        assert to_str(result) == "0"

    def test_count_single(self):
        result = self.expander.expand(r"\tl_count:n { x }")
        assert to_str(result) == "1"


class TestTlIfHeadEqMeaning:
    r"""Test \tl_if_head_eq_meaning:nNTF and variants."""

    def setup_method(self):
        self.expander = Expander()
        self.expander.expand(r"\ExplSyntaxOn")

    def test_TF_match_takes_true(self):
        r"""When head matches, take true branch."""
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNTF { abc } a { TRUE } { FALSE }"
        )
        assert to_str(result) == "TRUE"

    def test_TF_mismatch_takes_false(self):
        r"""When head doesn't match, take false branch."""
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNTF { abc } x { TRUE } { FALSE }"
        )
        assert to_str(result) == "FALSE"

    def test_T_match_produces_true(self):
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNT { abc } a { TRUE }"
        )
        assert to_str(result) == "TRUE"

    def test_T_mismatch_produces_nothing(self):
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNT { abc } x { TRUE }"
        )
        stripped = strip_whitespace_tokens(result)
        assert len(stripped) == 0

    def test_F_mismatch_produces_false(self):
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNF { abc } x { FALSE }"
        )
        assert to_str(result) == "FALSE"

    def test_F_match_produces_nothing(self):
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNF { abc } a { FALSE }"
        )
        stripped = strip_whitespace_tokens(result)
        assert len(stripped) == 0

    def test_cs_head_comparison(self):
        r"""Should match control sequence heads too."""
        result = self.expander.expand(
            r"\tl_if_head_eq_meaning:nNTF { \foo bar } \foo { TRUE } { FALSE }"
        )
        assert to_str(result) == "TRUE"
