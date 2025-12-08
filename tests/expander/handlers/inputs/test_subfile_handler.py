from typing import List
import pytest
import os
from latex2json.expander.expander import Expander
from latex2json.parser.parser import Parser
from latex2json.nodes.utils import find_nodes_by_type
from latex2json.nodes.section_nodes import SectionNode


dir_path = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(dir_path, "../../../samples/subfiles")


def test_subfile_handler_counter_continuity():
    r"""Test that subfiles maintain counter continuity when processed at expander level.

    This is the key test showing why \subfile needs to be at the expander level:
    Section counters must be sequential across all files (1, 2, 3, 4...).
    If \subfile was handled at parser level, each file would have its own
    counter context and numbering would restart.
    """
    parser = Parser()

    # Parse the main manuscript which includes subfiles
    filepath = os.path.join(test_data_path, "manuscript.tex")
    nodes = parser.parse_file(filepath, postprocess=True)

    # Find all section nodes
    section_nodes: List[SectionNode] = find_nodes_by_type(nodes, SectionNode)

    # Expected sections with sequential numbering across all files:
    # manuscript.tex: section 1
    # intro.tex: sections 2, 3 (two sections in intro.tex)
    # appendix.tex: section 4
    expected_sections = [
        ("section", "1", "sec:main", "manuscript.tex"),
        ("section", "2", "sec:intro", "intro.tex"),
        ("section", "3", "M-sec:fake", "intro.tex"),
        ("section", "4", "sec:appendix", "appendix.tex"),
    ]

    assert len(section_nodes) == len(expected_sections), (
        f"Expected {len(expected_sections)} sections, found {len(section_nodes)}"
    )

    # Verify each section has the correct sequential numbering
    for i, (sec_node, expected) in enumerate(zip(section_nodes, expected_sections)):
        exp_name, exp_numbering, exp_label, exp_source = expected

        assert sec_node.name == exp_name, (
            f"Section {i}: expected name '{exp_name}', got '{sec_node.name}'"
        )
        assert sec_node.numbering == exp_numbering, (
            f"Section {i}: expected numbering '{exp_numbering}', got '{sec_node.numbering}'. "
            f"This indicates counter continuity is broken!"
        )
        assert exp_label in sec_node.labels, (
            f"Section {i}: expected label '{exp_label}' in {sec_node.labels}"
        )
        assert sec_node.get_source_file() == exp_source, (
            f"Section {i}: expected source '{exp_source}', got '{sec_node.get_source_file()}'"
        )


def test_subfile_handler_expander_state():
    """Test that subfiles share expander state (macros, counters) with the main document."""
    expander = Expander()

    # Define a macro before loading subfile
    text = (
        r"""
    \newcounter{testcounter}
    \setcounter{testcounter}{5}
    \def\mymacro{DEFINED}

    \subfile{%s/intro.tex}
    """
        % test_data_path
    )

    tokens = expander.expand(text)

    # The counter should still exist after processing subfile
    # (not reset by subfile processing)
    counter_value = expander.state.get_counter_value("testcounter")
    assert counter_value is not None, "Counter should persist after subfile"

    # The macro should still be defined
    macro = expander.get_macro("mymacro")
    assert macro is not None, "Macro should persist after subfile"


def test_subfile_handler_basic():
    """Test basic subfile loading."""
    expander = Expander()

    # Load a subfile
    text = r"\subfile{%s/intro.tex}" % test_data_path
    tokens = expander.expand(text)

    # Should have processed the subfile and returned tokens
    assert len(tokens) > 0, "Should have tokens from subfile"

    # Check that we got content from the subfile
    token_str = "".join([t.value for t in tokens if hasattr(t, "value")])
    assert (
        "INTRO DOC" in token_str or "Intro" in token_str
    ), "Should contain content from intro.tex"


def test_subfile_nonexistent():
    """Test handling of nonexistent subfile."""
    expander = Expander()

    # Try to load a nonexistent subfile
    text = r"\subfile{nonexistent.tex}"
    tokens = expander.expand(text)

    # Should handle gracefully (may log warning but shouldn't crash)
    # The result should be an empty list or minimal tokens
    assert isinstance(tokens, list), "Should return a list even for nonexistent file"
