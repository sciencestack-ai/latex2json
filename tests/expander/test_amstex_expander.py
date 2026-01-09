import os
import pytest
from latex2json.expander.amstex_expander import AMSTeXExpander
from latex2json.expander.expander import Expander
from latex2json.parser import Parser
from latex2json.nodes import EnvironmentNode, strip_whitespace_nodes
from latex2json.nodes.utils import find_nodes_by_type
from latex2json.tokens import Token, TokenType


SAMPLES_DIR = os.path.join(os.path.dirname(__file__), "../samples")


class TestAMSTeXExpander:
    """Tests for AMSTeX to LaTeX token-based preprocessing."""

    def setup_method(self):
        self.expander = AMSTeXExpander()

    def _tokens_to_str(self, tokens):
        """Convert tokens to string for easier assertion."""
        return AMSTeXExpander.convert_tokens_to_str(tokens)

    def test_document_to_begin_document(self):
        """Test \\document -> \\begin{document}."""
        tokens = self.expander.process_text(r"\document")
        text = self._tokens_to_str(tokens)
        assert "\\begin{document}" in text

    def test_enddocument_to_end_document(self):
        """Test \\enddocument -> \\end{document}."""
        tokens = self.expander.process_text(r"\enddocument")
        text = self._tokens_to_str(tokens)
        assert "\\end{document}" in text

    def test_roster_to_itemize(self):
        """Test \\roster -> \\begin{itemize}."""
        tokens = self.expander.process_text(r"\roster")
        text = self._tokens_to_str(tokens)
        assert "\\begin{itemize}" in text

    def test_endroster_to_end_itemize(self):
        """Test \\endroster -> \\end{itemize}."""
        tokens = self.expander.process_text(r"\endroster")
        text = self._tokens_to_str(tokens)
        assert "\\end{itemize}" in text

    def test_demo_to_proof(self):
        """Test \\demo -> \\begin{proof}."""
        tokens = self.expander.process_text(r"\demo")
        text = self._tokens_to_str(tokens)
        assert "\\begin{proof}" in text

    def test_enddemo_to_end_proof(self):
        """Test \\enddemo -> \\end{proof}."""
        tokens = self.expander.process_text(r"\enddemo")
        text = self._tokens_to_str(tokens)
        assert "\\end{proof}" in text

    def test_refs_to_thebibliography(self):
        """Test \\Refs -> \\begin{thebibliography}."""
        tokens = self.expander.process_text(r"\Refs")
        text = self._tokens_to_str(tokens)
        assert "\\begin{thebibliography}" in text

    def test_define_to_def(self):
        """Test \\define -> \\def."""
        tokens = self.expander.process_text(r"\define\foo{bar}")
        text = self._tokens_to_str(tokens)
        assert "\\def" in text
        assert "\\foo" in text

    def test_bold_to_mathbf(self):
        """Test \\bold -> \\mathbf."""
        tokens = self.expander.process_text(r"\bold")
        text = self._tokens_to_str(tokens)
        assert "\\mathbf" in text

    def test_cal_to_mathcal(self):
        """Test \\Cal -> \\mathcal."""
        tokens = self.expander.process_text(r"\Cal")
        text = self._tokens_to_str(tokens)
        assert "\\mathcal" in text

    def test_bbb_to_mathbb(self):
        """Test \\Bbb -> \\mathbb."""
        tokens = self.expander.process_text(r"\Bbb")
        text = self._tokens_to_str(tokens)
        assert "\\mathbb" in text

    def test_nologo_removed(self):
        """Test that \\nologo is removed."""
        tokens = self.expander.process_text(r"\nologo hello")
        text = self._tokens_to_str(tokens)
        assert "\\nologo" not in text
        assert "hello" in text

    def test_tagsonright_removed(self):
        """Test that \\TagsOnRight is removed."""
        tokens = self.expander.process_text(r"\TagsOnRight")
        text = self._tokens_to_str(tokens)
        assert "\\TagsOnRight" not in text

    def test_preserves_regular_text(self):
        """Test that regular text is preserved."""
        tokens = self.expander.process_text("Hello world")
        text = self._tokens_to_str(tokens)
        assert "Hello world" in text

    def test_preserves_regular_commands(self):
        """Test that regular LaTeX commands are preserved."""
        tokens = self.expander.process_text(r"\section{Title}")
        text = self._tokens_to_str(tokens)
        assert "\\section" in text

    def test_full_document(self):
        """Test processing of a full AMSTeX document snippet."""
        amstex_doc = r"""
\document
\nologo
\define\foo{bar}

\proclaim{Theorem 1}
A theorem statement.
\endproclaim

\demo
The proof.
\enddemo

\enddocument
"""
        tokens = self.expander.process_text(amstex_doc)
        text = self._tokens_to_str(tokens)

        # Check conversions
        assert "\\begin{document}" in text
        assert "\\end{document}" in text
        assert "\\def" in text
        # assert "\\begin{proclaim}" in text
        # assert "\\end{proclaim}" in text
        assert "\\begin{proof}" in text
        assert "\\end{proof}" in text

        # Check removals
        assert "\\nologo" not in text

    def test_topmatter(self):
        """Test \\topmatter/\\endtopmatter."""
        tokens = self.expander.process_text(r"\topmatter content \endtopmatter")
        text = self._tokens_to_str(tokens)
        assert "\\begin{topmatter}" in text
        assert "\\end{topmatter}" in text

    def test_multiple_commands_in_sequence(self):
        """Test multiple AMSTeX commands in sequence."""
        tokens = self.expander.process_text(r"\bold\Cal\Bbb")
        text = self._tokens_to_str(tokens)
        assert "\\mathbf" in text
        assert "\\mathcal" in text
        assert "\\mathbb" in text

    def test_process_tokens(self):
        """Test processing already-tokenized content."""
        # Create some tokens manually
        input_tokens = [
            Token(TokenType.CONTROL_SEQUENCE, "document"),
            Token(TokenType.CHARACTER, " ", catcode=10),  # space
            Token(TokenType.CHARACTER, "H"),
            Token(TokenType.CHARACTER, "i"),
        ]
        self.expander.push_tokens(input_tokens)
        output_tokens = self.expander.process()
        text = self._tokens_to_str(output_tokens)
        assert "\\begin{document}" in text
        assert "Hi" in text


class TestAMSTeXIntegration:
    """Integration tests for AMSTeX file processing through the full pipeline."""

    def test_parse_amstex_file(self):
        """Test parsing an actual AMSTeX file through the parser."""
        parser = Parser()
        filepath = os.path.join(SAMPLES_DIR, "amstex_sample.tex")
        nodes = parser.parse_file(filepath)
        nodes = strip_whitespace_nodes(nodes)

        # Should have parsed successfully
        assert len(nodes) >= 1

        # Find document environment (proves \document -> \begin{document} worked)
        doc_nodes = find_nodes_by_type(nodes, EnvironmentNode)
        doc_envs = [n for n in doc_nodes if n.name == "document"]
        assert len(doc_envs) == 1

    def test_amstex_detection_in_push_text(self):
        """Test that AMSTeX is detected when text is pushed (e.g., via \\input)."""

        expander = Expander()

        # Push AMSTeX content - should be automatically preprocessed
        amstex_content = r"""
\input amstex
\topmatter
\title Test\endtitle
\endtopmatter
\document
Hello world.

\proclaim{conjecture}
This is a conjecture.
\endproclaim

\enddocument
"""
        expander.push_text(amstex_content)
        tokens = expander.process()
        text = expander.convert_tokens_to_str(tokens)

        # Verify AMSTeX was converted to LaTeX
        assert "\\begin{topmatter}" in text
        assert "\\begin{document}" in text
        assert "\\end{document}" in text

        assert "\\begin{conjecture}" in text
        assert "\\end{conjecture}" in text
