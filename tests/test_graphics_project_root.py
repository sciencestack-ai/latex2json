"""Test that includegraphics can find images in project_root for non-standard layouts."""

from latex2json.parser.parser import Parser
from latex2json.nodes import IncludeGraphicsNode
from latex2json.nodes.utils import find_nodes_by_type
import os


def test_includegraphics_with_graphicspath():
    """Test that graphicspath works with non-standard layouts using project_root fallback."""
    parser = Parser()

    # Simulate non-standard layout: main.tex is in samples/, but images/ is at project root
    samples_dir = os.path.join(
        os.path.dirname(__file__), "samples", "non_standard_layout", "samples"
    )
    project_root = os.path.join(
        os.path.dirname(__file__), "samples", "non_standard_layout"
    )
    main_tex = os.path.join(samples_dir, "main.tex")

    nodes = parser.parse_file(main_tex, project_root=project_root)

    # Find IncludeGraphicsNode (search recursively)
    graphics_nodes = find_nodes_by_type(nodes, IncludeGraphicsNode)

    # Should find the image reference from \graphicspath{{../images/}}
    assert len(graphics_nodes) > 0

    # The path should be relative to project_root (not absolute)
    for node in graphics_nodes:
        # Should be relative path like "images/test_image.pdf"
        assert not os.path.isabs(node.path), f"Expected relative path, got: {node.path}"
        assert "image" in node.path.lower()
        # Verify it's actually relative to project_root, not cwd
        assert node.path == "images/test_image.pdf"


def test_includegraphics_direct_path_to_project_root():
    """Test that includegraphics can find images directly at project_root without graphicspath."""
    parser = Parser()

    # Parse a simple document that references images/test.pdf directly
    text = r"""
    \documentclass{article}
    \usepackage{graphicx}
    \begin{document}
    \includegraphics{images/test_image.pdf}
    \end{document}
    """

    project_root = os.path.join(
        os.path.dirname(__file__), "samples", "non_standard_layout"
    )
    # Simulate that we're parsing from a subdirectory
    cwd = os.path.join(project_root, "samples")

    parser.cwd = cwd
    parser.project_root = project_root

    nodes = parser.parse(text)
    graphics_nodes = find_nodes_by_type(nodes, IncludeGraphicsNode)

    assert len(graphics_nodes) == 1
    # Path should be relative to project_root
    assert graphics_nodes[0].path == "images/test_image.pdf"
    assert not os.path.isabs(graphics_nodes[0].path)
