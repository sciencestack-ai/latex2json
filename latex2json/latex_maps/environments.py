import dataclasses
from enum import Enum
from typing import Any, Callable, List, Optional
from latex2json.tokens.types import EnvironmentType, Token


@dataclasses.dataclass
class Hooks:
    begin: List[Callable[..., List[Token]]] = dataclasses.field(
        default_factory=list
    )  # e.g. for AtBeginDocument etc
    end: List[Callable[..., List[Token]]] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class EnvironmentDefinition:
    name: str
    begin_handler: Optional[Callable] = None
    end_handler: Optional[Callable] = None
    display_name: Optional[str] = None

    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        begin_definition: List[Token] = [],
        end_definition: List[Token] = [],
        num_args: int = 0,
        default_arg: Optional[List[Token]] = None,
        counter_name: Optional[str] = None,  # e.g. "equation"
        env_type: EnvironmentType = EnvironmentType.DEFAULT,
        has_direct_command: bool = False,  # e.g. \begin{document} -> \document + \enddocument
        begin_command: Optional[str] = None,
        end_command: Optional[str] = None,
        is_float_env=False,
    ):
        self.name = name
        if not display_name:
            display_name = name
        self.display_name = display_name
        self.begin_definition = begin_definition
        self.end_definition = end_definition
        self.num_args = num_args
        self.default_arg = default_arg
        self.counter_name = counter_name
        self.env_type = env_type
        self.has_direct_command = has_direct_command
        self.begin_command = begin_command  # e.g. direct \beginpicture
        self.end_command = end_command  # e.g. direct \endpicture
        self.is_float_env = is_float_env

        # other state e.g. hooks
        self.hooks = Hooks()

        if has_direct_command:
            if not self.begin_command:
                self.begin_command = name
            if not self.end_command:
                self.end_command = "end" + name

    def copy(self) -> "EnvironmentDefinition":
        new_env = EnvironmentDefinition(
            name=self.name,
            begin_definition=self.begin_definition.copy(),
            end_definition=self.end_definition.copy(),
            num_args=self.num_args,
            default_arg=(
                self.default_arg.copy() if self.default_arg is not None else None
            ),
            counter_name=self.counter_name,
            env_type=self.env_type,
            has_direct_command=self.has_direct_command,
            begin_command=self.begin_command,
            end_command=self.end_command,
            is_float_env=self.is_float_env,
        )
        new_env.hooks = Hooks(begin=self.hooks.begin.copy(), end=self.hooks.end.copy())
        return new_env

    def __str__(self) -> str:
        out = f"EnvDef('{self.name}'"
        if self.num_args:
            out += f", num_args={self.num_args}"
        if self.default_arg is not None:
            out += f", default_arg={self.default_arg}"
        if self.begin_definition:
            out += f", begin_definition={self.begin_definition}"
        if self.end_definition:
            out += f", end_definition={self.end_definition}"
        if self.env_type != EnvironmentType.DEFAULT:
            out += f", env_type={self.env_type.name}"
        if self.counter_name:
            out += f", counter_name={self.counter_name}"
        if self.has_direct_command:
            out += ", has_direct_command=True"
        if self.is_float_env:
            out += ", is_float_env=True"
        return out + ")"

    def __repr__(self) -> str:
        return self.__str__()


# Document structure environments
DOCUMENT_ENVIRONMENTS = {
    "document": EnvironmentDefinition("document", has_direct_command=True),
    "abstract": EnvironmentDefinition("abstract"),
    "thebibliography": EnvironmentDefinition(
        "thebibliography", num_args=1, has_direct_command=True
    ),
    "appendix": EnvironmentDefinition("appendix"),
    "appendices": EnvironmentDefinition("appendices"),
    "quote": EnvironmentDefinition("quote", has_direct_command=True),
}

VERBATIM_ENVIRONMENTS = {
    "verbatim": EnvironmentDefinition(
        "verbatim", has_direct_command=True, env_type=EnvironmentType.VERBATIM
    ),
    "lstlisting": EnvironmentDefinition(
        "lstlisting", env_type=EnvironmentType.VERBATIM
    ),
    "minted": EnvironmentDefinition(
        "minted", env_type=EnvironmentType.VERBATIM, num_args=2, default_arg=[]
    ),
    "comment": EnvironmentDefinition("comment", env_type=EnvironmentType.VERBATIM),
}

ALGORITHM_ENVIRONMENTS = {
    "algorithm": EnvironmentDefinition(
        "algorithm", num_args=1, default_arg=[], is_float_env=True
    ),
    "algorithm*": EnvironmentDefinition(
        "algorithm*", num_args=1, default_arg=[], is_float_env=True
    ),
    "algorithmic": EnvironmentDefinition(
        "algorithmic", env_type=EnvironmentType.VERBATIM, num_args=1, default_arg=[]
    ),
}

PICTURE_ENVIRONMENTS = {
    # picture/tikz
    "picture": EnvironmentDefinition("picture", env_type=EnvironmentType.VERBATIM),
    "pspicture": EnvironmentDefinition(
        "pspicture", env_type=EnvironmentType.VERBATIM, has_direct_command=True
    ),
    "CD": EnvironmentDefinition("CD", env_type=EnvironmentType.VERBATIM),
    "beginpicture": EnvironmentDefinition(
        "picture",
        env_type=EnvironmentType.VERBATIM,
        begin_command="beginpicture",
        end_command="endpicture",
    ),
    "tikzcd": EnvironmentDefinition("tikzcd", env_type=EnvironmentType.VERBATIM),
    "tikzpicture": EnvironmentDefinition(
        "tikzpicture", env_type=EnvironmentType.VERBATIM
    ),
    "circuitikz": EnvironmentDefinition(
        "circuitikz", env_type=EnvironmentType.VERBATIM
    ),
    "pgfpicture": EnvironmentDefinition(
        "pgfpicture", env_type=EnvironmentType.VERBATIM
    ),
    "overpic": EnvironmentDefinition("overpic", env_type=EnvironmentType.VERBATIM),
}

# Text formatting and layout environments
LAYOUT_ENVIRONMENTS = {
    "titlepage": EnvironmentDefinition("titlepage"),
    "center": EnvironmentDefinition("center"),
    "centering": EnvironmentDefinition("centering"),
    "verse": EnvironmentDefinition("verse"),
    "tcolorbox": EnvironmentDefinition("tcolorbox", num_args=1, default_arg=[]),
    "flushleft": EnvironmentDefinition("flushleft"),
    "flushright": EnvironmentDefinition("flushright"),
    "small": EnvironmentDefinition("small"),
    "spacing": EnvironmentDefinition("spacing", num_args=1),
    "minipage": EnvironmentDefinition(
        "minipage", num_args=2, default_arg=[], has_direct_command=True
    ),
    "multicols": EnvironmentDefinition("multicols", num_args=1),
    "adjustbox": EnvironmentDefinition("adjustbox", num_args=1),
    "adjustwidth": EnvironmentDefinition("adjustwidth", num_args=2),
    "CJK": EnvironmentDefinition("CJK", num_args=2),
    "CJK*": EnvironmentDefinition("CJK*", num_args=2),
    # changepage
    "changemargin": EnvironmentDefinition("changemargin", num_args=2),
    # parcolumns e.g. \begin{parcolumns}[rulebetween]{2}
    "parcolumns": EnvironmentDefinition("parcolumns", num_args=2, default_arg=[]),
    "copyrightbox": EnvironmentDefinition("copyrightbox", num_args=1, default_arg=[]),
    "noticebox": EnvironmentDefinition("noticebox", num_args=1, default_arg=[]),
}


FIGURE_ENVIRONMENTS = {
    # figures
    "figure": EnvironmentDefinition(
        "figure", num_args=1, default_arg=[], has_direct_command=True, is_float_env=True
    ),
    "figure*": EnvironmentDefinition(
        "figure", num_args=1, default_arg=[], is_float_env=True
    ),
    "wrapfigure": EnvironmentDefinition(
        "figure", num_args=3, default_arg=[], is_float_env=True
    ),
    "subfigure": EnvironmentDefinition(
        "subfigure", num_args=2, default_arg=[], is_float_env=True
    ),
}

TABLE_ENVIRONMENTS = {
    "table": EnvironmentDefinition(
        "table", num_args=1, default_arg=[], has_direct_command=True, is_float_env=True
    ),
    "table*": EnvironmentDefinition(
        "table", num_args=1, default_arg=[], is_float_env=True
    ),
    "wraptable": EnvironmentDefinition(
        "table", num_args=3, default_arg=[], is_float_env=True
    ),
    "subtable": EnvironmentDefinition(
        "subtable", num_args=2, default_arg=[], is_float_env=True
    ),
}

TABULAR_ENVIRONMENTS = {
    "tabular": EnvironmentDefinition(
        "tabular", num_args=2, default_arg=[], has_direct_command=True
    ),
    "tabu": EnvironmentDefinition("tabular", num_args=2, default_arg=[]),
    "tabular*": EnvironmentDefinition("tabular", num_args=2, default_arg=[]),
    "tabularx": EnvironmentDefinition("tabular", num_args=2),
    "tabularx*": EnvironmentDefinition("tabular", num_args=2),
    "tabulary": EnvironmentDefinition("tabular", num_args=1),
    "longtable": EnvironmentDefinition("tabular", num_args=1),
    "longtable*": EnvironmentDefinition("tabular", num_args=1),
    # NiceTabular args are {...}[...] - ensure to handle separately downstream
    "NiceTabular": EnvironmentDefinition("NiceTabular"),
    "NiceTabular*": EnvironmentDefinition("NiceTabular*"),
    "NiceTabularX": EnvironmentDefinition("NiceTabularX"),
}

# List environments
LIST_ENVIRONMENTS = {
    "list": EnvironmentDefinition(
        "list", num_args=2, has_direct_command=True, env_type=EnvironmentType.LIST
    ),
    "trivlist": EnvironmentDefinition(
        "trivlist", has_direct_command=True, env_type=EnvironmentType.LIST
    ),
    "itemize": EnvironmentDefinition(
        "itemize",
        num_args=1,
        default_arg=[],
        has_direct_command=True,
        env_type=EnvironmentType.LIST,
    ),
    "enumerate": EnvironmentDefinition(
        "enumerate",
        num_args=1,
        default_arg=[],
        has_direct_command=True,
        env_type=EnvironmentType.LIST,
    ),  # enumitem package has [] arg
    "description": EnvironmentDefinition(
        "description",
        num_args=1,
        default_arg=[],
        has_direct_command=True,
        env_type=EnvironmentType.LIST,
    ),
    # * versions from enumitem package. Retain * for downstream parser to check inline
    "itemize*": EnvironmentDefinition(
        "itemize*", num_args=1, default_arg=[], env_type=EnvironmentType.LIST
    ),
    "enumerate*": EnvironmentDefinition(
        "enumerate*", num_args=1, default_arg=[], env_type=EnvironmentType.LIST
    ),
    "description*": EnvironmentDefinition(
        "description*", num_args=1, default_arg=[], env_type=EnvironmentType.LIST
    ),
}

# Mathematical environments
MATH_ENVIRONMENTS = {
    # standalone equation environments
    "equation": EnvironmentDefinition(
        "equation",
        counter_name="equation",
        env_type=EnvironmentType.EQUATION,
        has_direct_command=True,
    ),
    "equation*": EnvironmentDefinition(
        "equation*",
        env_type=EnvironmentType.EQUATION,
    ),
    "math": EnvironmentDefinition(  # equivalent to inline math
        "math",
        env_type=EnvironmentType.EQUATION,
    ),
    "displaymath": EnvironmentDefinition(  # equivalent to inline math
        "displaymath",
        env_type=EnvironmentType.EQUATION,
    ),
    "multline": EnvironmentDefinition(
        "multline", counter_name="equation", env_type=EnvironmentType.EQUATION
    ),
    "multline*": EnvironmentDefinition("multline*", env_type=EnvironmentType.EQUATION),
    "dmath": EnvironmentDefinition(
        "dmath", counter_name="equation", env_type=EnvironmentType.EQUATION
    ),
    "dmath*": EnvironmentDefinition("dmath*", env_type=EnvironmentType.EQUATION),
    # inner environments inside equation/align
    "gathered": EnvironmentDefinition(
        "gathered", env_type=EnvironmentType.EQUATION, has_direct_command=True
    ),
    "multlined": EnvironmentDefinition("multlined", env_type=EnvironmentType.EQUATION),
    # array types
    "aligned": EnvironmentDefinition(
        "aligned",
        env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY,
        has_direct_command=True,
    ),
    "alignedat": EnvironmentDefinition(
        "alignedat",
        num_args=1,
        env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY,
        has_direct_command=True,
    ),
    "array": EnvironmentDefinition(
        "array",
        num_args=2,
        default_arg=[],
        env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY,
        has_direct_command=True,
    ),
    "subarray": EnvironmentDefinition(
        "subarray",
        num_args=1,
        env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY,
        # has_direct_command=True,
    ),
    "cases": EnvironmentDefinition(
        "cases", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),
    "dcases": EnvironmentDefinition(
        "dcases", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),
    "split": EnvironmentDefinition(
        "split", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),
    # matrix envs (also inner envs)
    "matrix": EnvironmentDefinition(
        "matrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),
    "pmatrix": EnvironmentDefinition(
        "pmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),  # parentheses ()
    "bmatrix": EnvironmentDefinition(
        "bmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),  # brackets []
    "Bmatrix": EnvironmentDefinition(
        "Bmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),  # braces {}
    "vmatrix": EnvironmentDefinition(
        "vmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),  # vert bars | |
    "Vmatrix": EnvironmentDefinition(
        "Vmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),  # double vert bars || ||
    "smallmatrix": EnvironmentDefinition(
        "smallmatrix", env_type=EnvironmentType.EQUATION_MATRIX_OR_ARRAY
    ),
    # align environments
    "align": EnvironmentDefinition("align", env_type=EnvironmentType.EQUATION_ALIGN),
    "align*": EnvironmentDefinition("align*", env_type=EnvironmentType.EQUATION_ALIGN),
    "eqnarray": EnvironmentDefinition("align", env_type=EnvironmentType.EQUATION_ALIGN),
    "eqnarray*": EnvironmentDefinition(
        "align*", env_type=EnvironmentType.EQUATION_ALIGN
    ),
    "gather": EnvironmentDefinition("gather", env_type=EnvironmentType.EQUATION_ALIGN),
    "gather*": EnvironmentDefinition(
        "gather*", env_type=EnvironmentType.EQUATION_ALIGN
    ),
    "flalign": EnvironmentDefinition(
        "flalign", env_type=EnvironmentType.EQUATION_ALIGN
    ),
    "flalign*": EnvironmentDefinition(
        "flalign*", env_type=EnvironmentType.EQUATION_ALIGN
    ),
    "alignat": EnvironmentDefinition(
        "alignat",
        num_args=1,
        env_type=EnvironmentType.EQUATION_ALIGN,
    ),
    "alignat*": EnvironmentDefinition(
        "alignat*",
        num_args=1,
        env_type=EnvironmentType.EQUATION_ALIGN,
    ),
    # subequations
    "subequations": EnvironmentDefinition("subequations"),
}

# Theorem-like environments
THEOREM_ENVIRONMENTS = {
    "theorem": EnvironmentDefinition(
        "theorem", counter_name="theorem", env_type=EnvironmentType.THEOREM
    ),
    "lemma": EnvironmentDefinition(
        "lemma", counter_name="lemma", env_type=EnvironmentType.THEOREM
    ),
    "corollary": EnvironmentDefinition(
        "corollary", counter_name="corollary", env_type=EnvironmentType.THEOREM
    ),
    "proposition": EnvironmentDefinition(
        "proposition", counter_name="proposition", env_type=EnvironmentType.THEOREM
    ),
    "definition": EnvironmentDefinition(
        "definition", counter_name="definition", env_type=EnvironmentType.THEOREM
    ),
    "remark": EnvironmentDefinition(
        "remark", counter_name="remark", env_type=EnvironmentType.THEOREM
    ),
    "proof": EnvironmentDefinition("proof", env_type=EnvironmentType.THEOREM),
    "proof*": EnvironmentDefinition("proof", env_type=EnvironmentType.THEOREM),
}

# Combine all environment dictionaries
COMMON_ENVIRONMENTS = {
    **DOCUMENT_ENVIRONMENTS,
    **VERBATIM_ENVIRONMENTS,
    **PICTURE_ENVIRONMENTS,
    **LAYOUT_ENVIRONMENTS,
    **FIGURE_ENVIRONMENTS,
    **TABLE_ENVIRONMENTS,
    **TABULAR_ENVIRONMENTS,
    **LIST_ENVIRONMENTS,
    **MATH_ENVIRONMENTS,
    **ALGORITHM_ENVIRONMENTS,
    **THEOREM_ENVIRONMENTS,
}

# STAR_VARIANTS = [
#     "tabularx",
#     "longtable",
#     # "theorem",  # when using amsthm package
#     # "lemma",  # when using amsthm package
# ]

# for env in STAR_VARIANTS:
#     env_def = COMMON_ENVIRONMENTS.get(env)
#     if not env_def:
#         continue
#     env_star = env_def.copy()
#     env_star.name = env_star.name + "*"
#     env_star.has_direct_command = False
#     env_star.counter_name = None
#     COMMON_ENVIRONMENTS[env + "*"] = env_star
