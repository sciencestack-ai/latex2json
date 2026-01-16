"""Tests for expl3 peek handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestPeekCatcode:
    """Test peek_catcode:NTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_peek_catcode_TF_match_begin_group(self):
        """peek_catcode:NTF should match BEGIN_GROUP catcode."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NTF { { YES } { NO }
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_peek_catcode_TF_no_match(self):
        """peek_catcode:NTF should not match different catcodes."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NTF X { YES } { NO }
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_peek_catcode_TF_match_letter(self):
        """peek_catcode:NTF should match LETTER catcode."""
        # After consuming A as test token, peek at B which is also LETTER
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NTF A B { YES } { NO }
\ExplSyntaxOff
""")
        # B matches A's catcode (LETTER), so YES is pushed
        # but B remains in input
        assert "YES" in to_str(result)

    def test_peek_catcode_T_match(self):
        """peek_catcode:NT should execute true branch on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NT { { YES }
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_peek_catcode_T_no_match(self):
        """peek_catcode:NT should produce nothing on no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NT X { YES } REMAINING
\ExplSyntaxOff
""")
        # X doesn't match {, so true branch not executed
        # { YES } gets parsed as the branch but not pushed
        # REMAINING should be left
        assert "REMAINING" in to_str(result)
        assert "YES" not in to_str(result)

    def test_peek_catcode_F_no_match(self):
        """peek_catcode:NF should execute false branch on no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NF X { NO }
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_peek_catcode_F_match(self):
        """peek_catcode:NF should produce nothing on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_catcode:NF { { NO } REMAINING
\ExplSyntaxOff
""")
        # { matches {, so false branch not executed
        assert "REMAINING" in to_str(result)
        assert "NO" not in to_str(result)


class TestPeekMeaning:
    """Test peek_meaning:NTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_peek_meaning_TF_match_character(self):
        """peek_meaning:NTF should match same character tokens."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_meaning:NTF { { YES } { NO }
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_peek_meaning_TF_no_match_different_chars(self):
        """peek_meaning:NTF should not match different characters."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_meaning:NTF X { YES } { NO }
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_peek_meaning_T_match(self):
        """peek_meaning:NT should execute on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_meaning:NT { { YES }
\ExplSyntaxOff
""")
        assert to_str(result) == "YES"

    def test_peek_meaning_T_no_match(self):
        """peek_meaning:NT should not execute on no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_meaning:NT X { YES } REMAINING
\ExplSyntaxOff
""")
        assert "REMAINING" in to_str(result)
        assert "YES" not in to_str(result)

    def test_peek_meaning_F_no_match(self):
        """peek_meaning:NF should execute on no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_meaning:NF X { NO }
\ExplSyntaxOff
""")
        assert to_str(result) == "NO"

    def test_peek_meaning_F_match(self):
        """peek_meaning:NF should not execute on match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\peek_meaning:NF { { NO } REMAINING
\ExplSyntaxOff
""")
        assert "REMAINING" in to_str(result)
        assert "NO" not in to_str(result)
