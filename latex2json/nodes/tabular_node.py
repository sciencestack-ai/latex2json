from typing import List
from latex2json.nodes.base_nodes import ASTNode, TextNode, check_asts_equal
from latex2json.nodes.environment_nodes import EnvironmentNode
from latex2json.nodes.node_types import NodeTypes


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

    @property
    def body(self) -> List[ASTNode]:
        return self.children

    def set_body(self, body: List[ASTNode]):
        self.set_children(body)

    def is_single_null_cell(self) -> bool:
        """Check if this is an empty cell."""
        return self.rowspan == 1 and self.colspan == 1 and len(self.children) == 0

    def is_plain_text_cell(self) -> bool:
        if len(self.children) != 1:
            return False
        if self.rowspan > 1 or self.colspan > 1:
            # multirow/multicolumn cells are not plain text cells
            return False
        single_node = self.children[0]
        if not isinstance(single_node, TextNode):
            return False
        if single_node.styles:
            # if the text node has styling, it's not a plain text cell
            return False
        return True

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
        out = ", ".join(child.__str__() for child in self.children)
        return "[" + out + "]"

    def to_json(self):
        result = super().to_json()
        result["type"] = "cell"
        result["content"] = [child.to_json() for child in self.children]
        if self.rowspan > 1:
            result["rowspan"] = self.rowspan
        if self.colspan > 1:
            result["colspan"] = self.colspan
        return result

    def copy(self):
        return CellNode(
            body=self.copy_nodes(self.children),
            rowspan=self.rowspan,
            colspan=self.colspan,
        )


class RowNode(ASTNode):
    def __init__(self, cells: List[CellNode] = []):
        super().__init__()
        self.cells = cells
        self.set_children(cells)

    @property
    def cols(self) -> int:
        """Returns the total number of columns this row spans."""
        return sum(cell.colspan for cell in self.cells)

    @property
    def rows(self) -> int:
        return len(self.cells)

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
        out = ", ".join(cell.__str__() for cell in self.cells)
        return "[" + out + "]"

    def to_json(self):
        result = super().to_json()
        result["type"] = NodeTypes.ROW
        result["content"] = [cell.to_json() for cell in self.cells]
        return result

    def copy(self):
        return RowNode(self.copy_nodes(self.cells))


class TabularNode(EnvironmentNode):
    def __init__(
        self,
        row_nodes: List[RowNode] = [],
        auto_correct_rowspans: bool = True,
        # alignment: str = "",
    ):
        super().__init__("tabular", body=row_nodes)
        # self.alignment = alignment

        # Automatically correct inconsistent rowspans by default
        if auto_correct_rowspans and row_nodes:
            self.correct_rowspans()

    @property
    def row_nodes(self) -> List[RowNode]:
        return self.children

    def get_row_col(self):
        """Get dimensions of the table."""
        rows = len(self.row_nodes)
        cols = max((row.cols for row in self.row_nodes), default=0)
        return {"rows": rows, "cols": cols}

    def build_cell_matrix(self) -> List[List[CellNode | None]]:
        """
        Build a 2D matrix representing the actual cell occupancy in the table.

        Each position [row_idx][col_idx] contains the CellNode that occupies that position,
        whether it's the origin cell or a cell spanning from a previous row/column.

        This properly handles multirow and multicolumn spans by tracking which cells
        are "occupied" by spanning cells from earlier positions.

        Returns:
            List[List[CellNode | None]]: 2D matrix where each position contains:
                - The CellNode that occupies this position (may be from a span)
                - None if the position is truly empty
        """
        max_cols = max((row.cols for row in self.row_nodes), default=0)
        max_rows = len(self.row_nodes)

        # Initialize matrix with None
        matrix = [[None for _ in range(max_cols)] for _ in range(max_rows)]

        # Fill matrix by processing each row
        for row_idx, row in enumerate(self.row_nodes):
            col_idx = 0
            for cell in row.cells:
                # Find next free column (skip columns occupied by previous spans)
                while col_idx < max_cols and matrix[row_idx][col_idx] is not None:
                    col_idx += 1

                if col_idx >= max_cols:
                    # Row has more cells than columns - should not happen in valid tables
                    break

                # Mark all positions occupied by this cell's span
                for r in range(row_idx, min(row_idx + cell.rowspan, max_rows)):
                    for c in range(col_idx, min(col_idx + cell.colspan, max_cols)):
                        matrix[r][c] = cell

                col_idx += cell.colspan

        return matrix

    def correct_rowspans(self, logger=None):
        """
        Automatically correct inconsistent rowspans to match actual cell occupancy.

        This examines each multirow cell and updates its rowspan to reflect the actual
        number of rows it occupies (based on subsequent rows having empty cells).

        Returns:
            dict: Correction results containing:
                - 'corrected': int - Number of rowspans corrected
                - 'corrections': List[dict] - List of corrections made
        """
        import logging

        if logger is None:
            logger = logging.getLogger(__name__)

        corrections = []

        if not self.row_nodes:
            return {"corrected": 0, "corrections": []}

        # Build a column position map for each row, assuming all rowspan=1
        row_cell_positions = []
        for row_idx, row in enumerate(self.row_nodes):
            positions = []
            col_idx = 0
            for cell in row.cells:
                positions.append(col_idx)
                col_idx += cell.colspan
            row_cell_positions.append(positions)

        # Validate and correct cells with rowspan > 1
        validated_cells = set()

        for row_idx, row in enumerate(self.row_nodes):
            for cell_idx, cell in enumerate(row.cells):
                if cell.rowspan > 1 and id(cell) not in validated_cells:
                    validated_cells.add(id(cell))

                    # Get the column position of this cell
                    col_pos = row_cell_positions[row_idx][cell_idx]

                    # Check subsequent rows to see if they have empty cells at this column
                    actual_rows_occupied = 1

                    for check_row_idx in range(
                        row_idx + 1, min(row_idx + cell.rowspan, len(self.row_nodes))
                    ):
                        check_row = self.row_nodes[check_row_idx]

                        # Find which cell (if any) is at col_pos in this row
                        cell_at_position = None
                        for check_cell_idx, check_cell in enumerate(check_row.cells):
                            check_cell_col = row_cell_positions[check_row_idx][
                                check_cell_idx
                            ]
                            if check_cell_col == col_pos:
                                cell_at_position = check_cell
                                break

                        if cell_at_position is None:
                            # No cell found at this position - row ended early
                            break

                        # Check if the cell is empty (which means it's a placeholder for the multirow)
                        if len(cell_at_position.body) == 0:
                            # Empty cell - this row is properly skipping the column
                            actual_rows_occupied += 1
                        else:
                            # Non-empty cell - the multirow doesn't actually span here
                            break

                    if actual_rows_occupied != cell.rowspan:
                        old_rowspan = cell.rowspan
                        cell.rowspan = actual_rows_occupied

                        correction = {
                            "row": row_idx,
                            "col": col_pos,
                            "old_rowspan": old_rowspan,
                            "new_rowspan": actual_rows_occupied,
                            "cell": cell,
                        }
                        corrections.append(correction)
                        logger.info(
                            f"Corrected rowspan at ({row_idx}, {col_pos}): "
                            f"{old_rowspan} -> {actual_rows_occupied}"
                        )

        return {"corrected": len(corrections), "corrections": corrections}

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
        result["type"] = NodeTypes.TABULAR
        content = []
        for row in self.row_nodes:
            row_json = []
            for cell in row.cells:
                # if cell.is_single_null_cell():
                #     row_json.append(None)
                # elif cell.is_plain_text_cell():
                #     # append single text str?
                #     text_node = cell.children[0]
                #     text_json = text_node.to_json()
                #     row_json.append(text_json["content"])
                # else:
                cell_json = cell.to_json()
                del cell_json["type"]
                row_json.append(cell_json)
            content.append(row_json)
        result["content"] = content
        return result

    def copy(self):
        return TabularNode(
            row_nodes=self.copy_nodes(self.row_nodes),
        )
