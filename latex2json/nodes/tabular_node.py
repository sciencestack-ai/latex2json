from typing import List
from latex2json.nodes.base_nodes import ASTNode, check_asts_equal


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
        self.set_children(body)

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def is_null_cell(self) -> bool:
        """Check if this is an empty cell."""
        return len(self.children) == 0

    def __eq__(self, other: ASTNode):
        if not isinstance(other, CellNode):
            return False
        return (
            self.rowspan == other.rowspan
            and self.colspan == other.colspan
            and check_asts_equal(self.children, other.children)
        )

    def detokenize(self) -> str:
        """Convert the cell node back to LaTeX source code."""
        content = "".join(child.detokenize() for child in self.children)

        # Apply multirow/multicolumn wrappers if needed
        if self.rowspan > 1:
            content = f"\\multirow{{{self.rowspan}}}{{*}}{{{content}}}"
        if self.colspan > 1:
            content = f"\\multicolumn{{{self.colspan}}}{{c}}{{{content}}}"

        return content

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = "tabular_cell"
        result["content"] = (
            [child.to_json() for child in self.children] if self.children else None
        )
        if self.rowspan > 1:
            result["rowspan"] = self.rowspan
        if self.colspan > 1:
            result["colspan"] = self.colspan
        return result


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
        return all(len(cell.children) == 0 for cell in self.cells)

    def __eq__(self, other: ASTNode):
        if not isinstance(other, RowNode):
            return False
        return all(a == b for a, b in zip(self.cells, other.cells))

    def detokenize(self) -> str:
        """Convert the row node back to LaTeX source code."""
        return " & ".join(cell.detokenize() for cell in self.cells)

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = "tabular_row"
        result["content"] = [cell.to_json() for cell in self.cells]
        return result


class TabularNode(ASTNode):
    def __init__(
        self,
        row_nodes: List[RowNode] = [],
        # alignment: str = "",
    ):
        super().__init__()
        # self.alignment = alignment
        self.set_children(row_nodes)

    @property
    def row_nodes(self) -> List[RowNode]:
        return self.children

    def get_row_col(self):
        """Get dimensions of the table."""
        rows = len(self.row_nodes)
        cols = max((row.cols for row in self.row_nodes), default=0)
        return {"rows": rows, "cols": cols}

    def __eq__(self, other: ASTNode):
        if not isinstance(other, TabularNode):
            return False
        # if self.alignment != other.alignment:
        #     return False
        return all(a == b for a, b in zip(self.children, other.children))

    def detokenize(self) -> str:
        """Convert the tabular node back to LaTeX source code."""
        # Add required packages for multirow/multicolumn support
        out = "\\begin{tabular}"

        if not self.row_nodes:
            return out + "\\end{tabular}"

        out += "\n"

        for i, row in enumerate(self.row_nodes):
            out += row.detokenize()
            if i < len(self.row_nodes) - 1:
                out += " \\\\\n"

        out += "\n\\end{tabular}"
        return out

    def __str__(self):
        return self.detokenize()

    def to_json(self):
        result = super().to_json()
        result["type"] = "tabular"
        content = []
        for row in self.row_nodes:
            row_json = []
            for cell in row.cells:
                if cell.is_null_cell() and cell.rowspan < 2 and cell.colspan < 2:
                    row_json.append(None)
                else:
                    cell_json = cell.to_json()
                    del cell_json["type"]
                    row_json.append(cell_json)
            content.append(row_json)
        result["content"] = content
        return result
