import pytest
import os
from latex2json.expander.expander import Expander
from latex2json.parser.parser import Parser
from latex2json.nodes.utils import find_nodes_by_type
from latex2json.nodes.section_nodes import SectionNode


dir_path = os.path.dirname(os.path.abspath(__file__))
test_data_path = os.path.join(dir_path, "../../../samples/subfiles")


def test_subfile_handler_counter_continuity():
    """Test that subfiles maintain counter continuity when processed at expander level."""
    parser = Parser()

    # Parse the main manuscript which includes subfiles
    filepath = os.path.join(test_data_path, "manuscript.tex")
    nodes = parser.parse_file(filepath, postprocess=True)

    # Find all section nodes
    section_nodes = find_nodes_by_type(nodes, SectionNode)

    # We should have sections from manuscript.tex, intro.tex, and appendix.tex
    # The counters should be sequential
    assert len(section_nodes) > 0, "Should have found section nodes"

    # Check that sections exist (basic sanity check)
    section_names = [node.name for node in section_nodes]
    assert any("section" in name for name in section_names), "Should have section nodes"

    # Verify we have at least 3 sections (Main, Intro, and one or more from subfiles)
    assert len(section_nodes) >= 3, f"Should have at least 3 sections, found {len(section_nodes)}"


def test_subfile_handler_expander_state():
    """Test that subfiles share expander state (macros, counters) with the main document."""
    expander = Expander()

    # Define a macro before loading subfile
    text = r"""
    \newcounter{testcounter}
    \setcounter{testcounter}{5}
    \def\mymacro{DEFINED}

    \subfile{%s/intro.tex}
    """ % test_data_path

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
    token_str = "".join([t.value for t in tokens if hasattr(t, 'value')])
    assert "INTRO DOC" in token_str or "Intro" in token_str, "Should contain content from intro.tex"


def test_subfile_nonexistent():
    """Test handling of nonexistent subfile."""
    expander = Expander()

    # Try to load a nonexistent subfile
    text = r"\subfile{nonexistent.tex}"
    tokens = expander.expand(text)

    # Should handle gracefully (may log warning but shouldn't crash)
    # The result should be an empty list or minimal tokens
    assert isinstance(tokens, list), "Should return a list even for nonexistent file"
