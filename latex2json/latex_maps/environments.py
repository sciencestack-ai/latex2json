import dataclasses
from typing import Callable, List, Optional
from latex2json.tokens.types import Token


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
        is_math: bool = False,  # e.g, align, equation, etc.
        is_verbatim: bool = False,
        has_direct_command: bool = False,  # e.g. \begin{document} -> \document + \enddocument
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
        self.is_math = is_math
        self.is_verbatim = is_verbatim
        self.has_direct_command = has_direct_command

    def copy(self) -> "EnvironmentDefinition":
        return EnvironmentDefinition(
            name=self.name,
            begin_definition=self.begin_definition.copy(),
            end_definition=self.end_definition.copy(),
            num_args=self.num_args,
            default_arg=(
                self.default_arg.copy() if self.default_arg is not None else None
            ),
            counter_name=self.counter_name,
            is_math=self.is_math,
            is_verbatim=self.is_verbatim,
            has_direct_command=self.has_direct_command,
        )

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
        if self.is_math:
            out += ", is_math=True"
        if self.is_verbatim:
            out += ", is_verbatim=True"
        if self.counter_name:
            out += f", counter_name={self.counter_name}"
        if self.has_direct_command:
            out += ", has_direct_command=True"
        return out + ")"

    def __repr__(self) -> str:
        return self.__str__()


# Document structure environments
DOCUMENT_ENVIRONMENTS = {
    "document": EnvironmentDefinition("document", has_direct_command=True),
    "abstract": EnvironmentDefinition("abstract", has_direct_command=True),
    "thebibliography": EnvironmentDefinition(
        "thebibliography", num_args=1, has_direct_command=True
    ),
}

VERBATIM_ENVIRONMENTS = {
    "quote": EnvironmentDefinition("quote", has_direct_command=True, is_verbatim=True),
    "verbatim": EnvironmentDefinition(
        "verbatim", has_direct_command=True, is_verbatim=True
    ),
    "lstlisting": EnvironmentDefinition("lstlisting", is_verbatim=True),
}

ALGORITHM_ENVIRONMENTS = {
    "algorithm": EnvironmentDefinition("algorithm"),
    "algorithmic": EnvironmentDefinition("algorithmic", is_verbatim=True),
}

PICTURE_ENVIRONMENTS = {
    # picture/tikz
    "picture": EnvironmentDefinition("picture", is_verbatim=True),
    "tikzpicture": EnvironmentDefinition("tikzpicture", is_verbatim=True),
    "pgfpicture": EnvironmentDefinition("pgfpicture", is_verbatim=True),
}

# Text formatting and layout environments
LAYOUT_ENVIRONMENTS = {
    "center": EnvironmentDefinition("center"),
    "spacing": EnvironmentDefinition("spacing", num_args=1),
    "minipage": EnvironmentDefinition("minipage", num_args=1, has_direct_command=True),
    "multicols": EnvironmentDefinition("multicols", num_args=1),
    "adjustbox": EnvironmentDefinition("adjustbox", num_args=1),
    "adjustwidth": EnvironmentDefinition("adjustwidth", num_args=2),
    "CJK": EnvironmentDefinition("CJK", num_args=2),
}


FIGURE_ENVIRONMENTS = {
    # figures
    "figure": EnvironmentDefinition(
        "figure", num_args=1, default_arg=[], has_direct_command=True
    ),
    "wrapfigure": EnvironmentDefinition(
        "figure",
        num_args=3,
        default_arg=[],
    ),
    "subfigure": EnvironmentDefinition(
        "subfigure",
        num_args=2,
        default_arg=[],
    ),
}

TABLE_ENVIRONMENTS = {
    "table": EnvironmentDefinition(
        "table", num_args=1, default_arg=[], has_direct_command=True
    ),
    "subtable": EnvironmentDefinition("subtable", num_args=2, default_arg=[]),
}

TABULAR_ENVIRONMENTS = {
    "tabular": EnvironmentDefinition("tabular", num_args=1, has_direct_command=True),
    "tabularx": EnvironmentDefinition("tabular", num_args=2),
    "tabulary": EnvironmentDefinition("tabular", num_args=1),
    "longtable": EnvironmentDefinition("tabular", num_args=1),
}

# List environments
LIST_ENVIRONMENTS = {
    "itemize": EnvironmentDefinition("itemize", has_direct_command=True),
    "enumerate": EnvironmentDefinition("enumerate", has_direct_command=True),
    "description": EnvironmentDefinition("description", has_direct_command=True),
    "list": EnvironmentDefinition("list", num_args=2, has_direct_command=True),
}

# Mathematical environments
MATH_ENVIRONMENTS = {
    "equation": EnvironmentDefinition(
        "equation", counter_name="equation", is_math=True, has_direct_command=True
    ),
    "align": EnvironmentDefinition("align", counter_name="equation", is_math=True),
    "aligned": EnvironmentDefinition("aligned", is_math=True),
    "gather": EnvironmentDefinition("gather", counter_name="equation", is_math=True),
    "multline": EnvironmentDefinition(
        "multline", counter_name="equation", is_math=True
    ),
    "eqnarray": EnvironmentDefinition(
        "eqnarray", counter_name="equation", is_math=True
    ),
    "flalign": EnvironmentDefinition("flalign", counter_name="equation", is_math=True),
    "alignat": EnvironmentDefinition(
        "alignat",
        num_args=1,
        counter_name="equation",
        is_math=True,
    ),
    "dmath": EnvironmentDefinition("dmath", counter_name="equation", is_math=True),
    "split": EnvironmentDefinition("split", is_math=True),
    "array": EnvironmentDefinition("array", num_args=1, is_math=True),
}

# # Theorem-like environments
# THEOREM_ENVIRONMENTS = {
#     "theorem": EnvironmentDefinition("theorem", step_counter=True),
#     "proof": EnvironmentDefinition("proof"),
# }

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
    # **THEOREM_ENVIRONMENTS,
}

STAR_VARIANTS = [
    "equation",
    "align",
    "gather",
    "multline",
    "eqnarray",  # though deprecated
    "flalign",
    "alignat",
    "dmath",
    "figure",
    "table",
    "tabular",
    "tabularx",
    "longtable",
    "theorem",  # when using amsthm package
    "lemma",  # when using amsthm package
    "proof",  # when using amsthm package
]

for env in STAR_VARIANTS:
    env_def = COMMON_ENVIRONMENTS.get(env)
    if not env_def:
        continue
    env_star = env_def.copy()
    env_star.name = env_star.name + "*"
    env_star.has_direct_command = False
    env_star.counter_name = None
    COMMON_ENVIRONMENTS[env_star.name] = env_star
