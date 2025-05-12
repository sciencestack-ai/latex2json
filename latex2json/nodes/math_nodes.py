from latex2json.nodes.base import ASTNode


class MathShiftNode(ASTNode):
    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return f"MathShift({self.text})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, MathShiftNode):
            return False
        return self.text == other.text


class EquationNode(ASTNode):
    def __init__(self, text: str, inline=False):
        self.text = text
        self.inline = inline

    def __str__(self):
        return f"Equation({self.text})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EquationNode):
            return False
        return self.text == other.text and self.inline == other.inline
