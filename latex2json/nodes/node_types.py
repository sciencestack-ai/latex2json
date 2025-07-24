from enum import Enum


class StrEnum(str, Enum):
    def __str__(self):
        return self.value


class NodeTypes(StrEnum):
    """Enum for node types"""

    # Document/Content Structure
    DOCUMENT = "document"
    TITLE = "title"
    SECTION = "section"
    PARAGRAPH = "paragraph"
    ABSTRACT = "abstract"
    APPENDIX = "appendix"

    COMMAND = "command"

    # Text
    TEXT = "text"
    QUOTE = "quote"

    # ENV related
    ENVIRONMENT = "environment"
    MATH_ENV = "math_env"
    # Tables & Figures
    FIGURE = "figure"
    SUBFIGURE = "subfigure"
    TABLE = "table"
    SUBTABLE = "subtable"
    TABULAR = "tabular"
    CAPTION = "caption"

    # Graphics
    INCLUDEGRAPHICS = "includegraphics"
    INCLUDEPDF = "includepdf"
    DIAGRAM = "diagram"

    # Lists
    LIST = "list"
    ITEM = "item"

    # Math & Technical
    EQUATION = "equation"
    EQUATION_ARRAY = "equation_array"
    ROW = "row"  # used in equation_array
    CODE = "code"  # for verbatim e.g. lstlisting
    ALGORITHM = "algorithm"
    ALGORITHMIC = "algorithmic"

    # References & Links
    CITATION = "citation"
    REF = "ref"
    URL = "url"
    FOOTNOTE = "footnote"

    # Bibliography
    BIBLIOGRAPHY = "bibliography"
    BIBITEM = "bibitem"

    # Metadata
    AUTHOR = "author"
    EMAIL = "email"
    AFFILIATION = "affiliation"
    KEYWORDS = "keywords"
    ADDRESS = "address"

    # Other
    GROUP = "group"

    def __eq__(self, other) -> bool:
        if isinstance(other, str):
            return self.value == other
        return super().__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}.{self.value.upper()}"

    def __str__(self) -> str:
        return self.value


if __name__ == "__main__":
    x = {"type": NodeTypes.CITATION, "content": "SSS"}
    print(x)
