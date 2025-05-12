import pytest
from latex2json.nodes.math_nodes import EquationNode


def test_equation_node():
    # Test inline equation
    inline_eq = EquationNode("x^2 + y^2 = z^2", inline=True)
    assert inline_eq.text == "x^2 + y^2 = z^2"
    assert inline_eq.inline is True

    # Test display equation
    display_eq = EquationNode("\\frac{1}{2}", inline=False)
    assert display_eq.text == "\\frac{1}{2}"
    assert display_eq.inline is False
    assert inline_eq != display_eq

    # Test equality
    assert inline_eq == EquationNode("x^2 + y^2 = z^2", inline=True)
    assert inline_eq != EquationNode("x^2 + y^2 = z^2", inline=False)
    assert inline_eq != EquationNode("different equation", inline=True)
