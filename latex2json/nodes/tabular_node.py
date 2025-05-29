from typing import List
from latex2json.nodes.base_nodes import ASTNode
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.utils import strip_whitespace_nodes


class CellNode(ASTNode):
    def __init__(
        self,
        body: List[ASTNode] = [],
        rowspan: int = 1,
        colspan: int = 1,
    ):
        super().__init__()
        self.rowspan = rowspan
        self.colspan = colspan
        self.set_body(body)

    def set_body(self, body: List[ASTNode]):
        self.body = body
        self.set_children(self.body)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CellNode):
            return False
        return (
            self.rowspan == other.rowspan
            and self.colspan == other.colspan
            and all(a == b for a, b in zip(self.body, other.body))
        )

    def detokenize(self) -> str:
        """Convert the cell node back to LaTeX source code."""
        content = "".join(child.detokenize() for child in self.body)

        # Apply multirow/multicolumn wrappers if needed
        if self.rowspan > 1:
            content = f"\\multirow{{{self.rowspan}}}{{*}}{{{content}}}"
        if self.colspan > 1:
            content = f"\\multicolumn{{{self.colspan}}}{{c}}{{{content}}}"

        return content

    def __str__(self):
        return self.detokenize()


class RowNode(ASTNode):
    def __init__(self, cells: List[CellNode] = []):
        super().__init__()
        self.cells = cells
        self.set_children(cells)

    @property
    def cols(self) -> int:
        """Returns the total number of columns this row spans."""
        return sum(cell.colspan for cell in self.cells)

    def is_null_row(self) -> bool:
        """Check if this is an empty row."""
        return all(len(cell.body) == 0 for cell in self.cells)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RowNode):
            return False
        return all(a == b for a, b in zip(self.cells, other.cells))

    def detokenize(self) -> str:
        """Convert the row node back to LaTeX source code."""
        return " & ".join(cell.detokenize() for cell in self.cells)

    def __str__(self):
        return self.detokenize()


class TabularNode(EnvironmentNode):
    def __init__(
        self,
        rows: List[RowNode] = [],
        # alignment: str = "",
    ):
        super().__init__("tabular", [])
        self.rows = rows
        # self.alignment = alignment
        self.set_children(rows)

    def get_row_col(self):
        """Get dimensions of the table."""
        rows = len(self.rows)
        cols = max((row.get_total_cols() for row in self.rows), default=0)
        return {"rows": rows, "cols": cols}

    def __eq__(self, other: ASTNode):
        if not isinstance(other, TabularNode):
            return False
        # if self.alignment != other.alignment:
        #     return False
        return all(a == b for a, b in zip(self.rows, other.rows))

    def detokenize(self) -> str:
        """Convert the tabular node back to LaTeX source code."""
        # Add required packages for multirow/multicolumn support
        out = "\\begin{tabular}"

        if not self.rows:
            return out + "\\end{tabular}"

        out += "\n"

        for i, row in enumerate(self.rows):
            out += row.detokenize()
            if i < len(self.rows) - 1:
                out += " \\\\\n"

        out += "\n\\end{tabular}"
        return out
