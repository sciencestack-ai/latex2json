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

    def detokenize(self):
        return self.text


class InlineEquationNode(ASTNode):
    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return self.detokenize()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, InlineEquationNode):
            return False
        return self.text == other.text

    def detokenize(self):
        return "$" + self.text + "$"


class DisplayEquationNode(ASTNode):
    def __init__(self, text: str, align=False, asterisk=False):
        self.text = text
        self.align = align
        self.asterisk = asterisk

    def __str__(self):
        return f"Equation({self.text})"

    def __eq__(self, other: ASTNode):
        if not isinstance(other, DisplayEquationNode):
            return False
        return self.text == other.text and self.align == other.align

    def detokenize(self):
        name = "align" if self.align else "equation"
        if self.asterisk:
            name += "*"
        out = f"\\begin{{{name}}}{self.text}\\end{{{name}}}"
        return out
