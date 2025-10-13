import pytest

import os

from traitlets import List
from latex2json.nodes.graphics_pdf_diagram_nodes import DiagramNode
from latex2json.nodes.utils import (
    find_nodes_by_type,
)
from latex2json.parser.parser import Parser

SAMPLES_DIR_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def test_diagram_sourcefiles():
    parser = Parser()
    out = parser.parse_file(
        os.path.join(SAMPLES_DIR_PATH, "diagram_sourcefiles/main.tex")
    )
    assert len(out) >= 1
    diagram_nodes: List[DiagramNode] = find_nodes_by_type(out, DiagramNode)
    assert len(diagram_nodes) == 4

    node1: DiagramNode = diagram_nodes[0]
    assert node1.env_name == "tikzpicture"
    assert node1.source_file == "intro.tex"

    node2: DiagramNode = diagram_nodes[1]
    assert node2.env_name == "xymatrix"
    assert node2.source_file == "sections/xymatrix.tex"

    node3: DiagramNode = diagram_nodes[2]
    assert node3.env_name == "circuitikz"
    assert node3.source_file == "sections/circuitikz.tex"

    node4: DiagramNode = diagram_nodes[3]
    assert node4.env_name == "tikzpicture"
    assert node4.source_file == "main.tex"
