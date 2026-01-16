"""Tests for expl3 regular expression (regex) handlers."""

import pytest
from latex2json.expander.expander import Expander
from latex2json.expander.token_processor import TokenProcessor


def to_str(tokens):
    """Helper to convert tokens to string."""
    return TokenProcessor.convert_tokens_to_str(tokens).strip()


class TestRegexMatch:
    """Test regex_match:nnTF and variants."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_match_simple_true(self):
        """regex_match:nnTF should match simple pattern."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_match:nnTF {abc} {xyzabcdef} {MATCH} {NOMATCH}
\ExplSyntaxOff
""")
        assert to_str(result) == "MATCH"

    def test_regex_match_simple_false(self):
        """regex_match:nnTF should not match when pattern not found."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_match:nnTF {xyz} {abcdef} {MATCH} {NOMATCH}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOMATCH"

    def test_regex_match_with_metachar(self):
        """regex_match:nnTF with regex metacharacters."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_match:nnTF {a+b} {aaab} {MATCH} {NOMATCH}
\ExplSyntaxOff
""")
        assert to_str(result) == "MATCH"

    def test_regex_match_digit_class(self):
        """regex_match:nnTF with digit character class."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_match:nnTF {\d+} {abc123def} {MATCH} {NOMATCH}
\ExplSyntaxOff
""")
        assert to_str(result) == "MATCH"

    def test_regex_match_T_variant(self):
        """regex_match:nnT only executes true branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\regex_match:nnT {test} {this is a test} {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XTRUEY"

    def test_regex_match_T_no_match(self):
        """regex_match:nnT does nothing when no match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\regex_match:nnT {xyz} {abcdef} {TRUE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_regex_match_F_variant(self):
        """regex_match:nnF only executes false branch."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\regex_match:nnF {xyz} {abcdef} {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XFALSEY"

    def test_regex_match_F_no_execute(self):
        """regex_match:nnF does nothing when match found."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
X\regex_match:nnF {abc} {abcdef} {FALSE}Y
\ExplSyntaxOff
""")
        assert to_str(result) == "XY"

    def test_regex_match_anchored(self):
        """regex_match:nnTF with anchored pattern."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_match:nnTF {^abc} {abcdef} {MATCH} {NOMATCH}
\ExplSyntaxOff
""")
        assert to_str(result) == "MATCH"

    def test_regex_match_anchored_fail(self):
        """regex_match:nnTF with anchored pattern that doesn't match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_match:nnTF {^abc} {xyzabc} {MATCH} {NOMATCH}
\ExplSyntaxOff
""")
        assert to_str(result) == "NOMATCH"


class TestRegexCount:
    """Test regex_count:nnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_count_multiple_matches(self):
        """regex_count:nnN should count all matches."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_new:N \l_count_int
\regex_count:nnN {a} {abracadabra} \l_count_int
\int_use:N \l_count_int
\ExplSyntaxOff
""")
        assert to_str(result) == "5"

    def test_regex_count_no_matches(self):
        """regex_count:nnN with no matches returns 0."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_new:N \l_count_int
\regex_count:nnN {xyz} {abcdef} \l_count_int
\int_use:N \l_count_int
\ExplSyntaxOff
""")
        assert to_str(result) == "0"

    def test_regex_count_overlapping(self):
        """regex_count:nnN counts non-overlapping matches."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\int_new:N \l_count_int
\regex_count:nnN {aa} {aaaa} \l_count_int
\int_use:N \l_count_int
\ExplSyntaxOff
""")
        # Should find 2 non-overlapping matches
        assert to_str(result) == "2"


class TestRegexReplaceOnce:
    """Test regex_replace_once:nnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_replace_once_basic(self):
        """regex_replace_once:nnN should replace first match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {hello_world_hello}
\regex_replace_once:nnN {hello} {goodbye} \l_my_tl
\l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "goodbye_world_hello"

    def test_regex_replace_once_no_match(self):
        """regex_replace_once:nnN with no match leaves string unchanged."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {hello_world}
\regex_replace_once:nnN {xyz} {abc} \l_my_tl
\l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "hello_world"


class TestRegexReplaceAll:
    """Test regex_replace_all:nnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_replace_all_basic(self):
        """regex_replace_all:nnN should replace all matches."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {hello_world_hello}
\regex_replace_all:nnN {hello} {goodbye} \l_my_tl
\l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "goodbye_world_goodbye"

    def test_regex_replace_all_simple(self):
        """regex_replace_all:nnN with simple pattern."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {aaa}
\regex_replace_all:nnN {a} {b} \l_my_tl
\l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "bbb"

    def test_regex_replace_all_no_match(self):
        """regex_replace_all:nnN with no match leaves string unchanged."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\tl_new:N \l_my_tl
\tl_set:Nn \l_my_tl {hello}
\regex_replace_all:nnN {x} {y} \l_my_tl
\l_my_tl
\ExplSyntaxOff
""")
        assert to_str(result) == "hello"


class TestRegexSplit:
    """Test regex_split:nnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_split_basic(self):
        """regex_split:nnN should split string by pattern."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_parts_seq
\regex_split:nnN {,} {a,b,c} \l_parts_seq
\seq_use:Nn \l_parts_seq {|}
\ExplSyntaxOff
""")
        assert to_str(result) == "a|b|c"

    def test_regex_split_dash(self):
        """regex_split:nnN with dash separator."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_parts_seq
\regex_split:nnN {-} {hello-world-foo} \l_parts_seq
\seq_use:Nn \l_parts_seq {|}
\ExplSyntaxOff
""")
        assert to_str(result) == "hello|world|foo"


class TestRegexNew:
    """Test regex_new:N and regex_set:Nn."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_new_creates_empty(self):
        """regex_new:N should create an empty regex variable."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_new:N \l_my_regex
\regex_set:Nn \l_my_regex {pattern}
\l_my_regex
\ExplSyntaxOff
""")
        # Verify it can be set after creation
        assert to_str(result) == "pattern"

    def test_regex_set_stores_pattern(self):
        """regex_set:Nn should store a pattern."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\regex_new:N \l_my_regex
\regex_set:Nn \l_my_regex {test}
\l_my_regex
\ExplSyntaxOff
""")
        assert to_str(result) == "test"


class TestRegexExtractOnce:
    """Test regex_extract_once:nnN."""

    def setup_method(self):
        self.expander = Expander()

    def test_regex_extract_once_basic(self):
        """regex_extract_once:nnN should extract first match."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_result_seq
\regex_extract_once:nnN {[0-9]+} {abc123def456} \l_result_seq
\seq_item:Nn \l_result_seq {1}
\ExplSyntaxOff
""")
        assert to_str(result) == "123"

    def test_regex_extract_once_no_match(self):
        """regex_extract_once:nnN with no match creates empty sequence."""
        result = self.expander.expand(r"""
\ExplSyntaxOn
\seq_new:N \l_result_seq
\regex_extract_once:nnN {[0-9]+} {abcdef} \l_result_seq
\seq_if_empty:NTF \l_result_seq {EMPTY} {NOTEMPTY}
\ExplSyntaxOff
""")
        assert to_str(result) == "EMPTY"
