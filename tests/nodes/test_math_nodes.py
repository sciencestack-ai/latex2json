# import pytest
# from latex2json.nodes.math_nodes import InlineEquationNode, DisplayEquationNode


# def test_equation_node():
#     # Test inline equation
#     inline_eq = InlineEquationNode("x^2 + y^2 = z^2")
#     assert inline_eq.text == "x^2 + y^2 = z^2"

#     # Test display equation
#     display_eq = DisplayEquationNode("\\frac{1}{2}")
#     assert display_eq.text == "\\frac{1}{2}"
#     assert display_eq.align is False
#     assert inline_eq != display_eq

#     # Test equality
#     assert inline_eq == InlineEquationNode("x^2 + y^2 = z^2")
#     assert inline_eq != DisplayEquationNode("x^2 + y^2 = z^2")
#     assert inline_eq != InlineEquationNode("different equation")
