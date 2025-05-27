import dataclasses
from typing import Callable, List, Optional
from latex2json.tokens.types import Token


@dataclasses.dataclass
class EnvironmentDefinition:
    name: str
    begin_handler: Optional[Callable] = None
    end_handler: Optional[Callable] = None

    def __init__(
        self,
        name: str,
        begin_definition: List[Token] = [],
        end_definition: List[Token] = [],
        num_args: int = 0,
        default_arg: Optional[List[Token]] = None,
        step_counter: bool = False,  # whether to increment counter for the env in begin block each time
        assign_counter: bool = True,  # whether to assign counter for the env in begin block. For table/figure, this should be False since captions are assigned counters
        is_math: bool = False,  # e.g, align, equation, etc.
        has_direct_command: bool = True,  # e.g. \begin{document} -> \document + \enddocument
    ):
        self.name = name
        self.begin_definition = begin_definition
        self.end_definition = end_definition
        self.num_args = num_args
        self.default_arg = default_arg
        self.step_counter = step_counter
        self.assign_counter = assign_counter
        self.is_math = is_math
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
            step_counter=self.step_counter,
            assign_counter=self.assign_counter,
            is_math=self.is_math,
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
        if self.step_counter:
            out += ", step_counter=True"
        if self.assign_counter:
            out += ", assign_counter=True"
        if self.has_direct_command:
            out += ", has_direct_command=True"
        return out + ")"

    def __repr__(self) -> str:
        return self.__str__()


# Document structure environments
DOCUMENT_ENVIRONMENTS = {
    "document": EnvironmentDefinition("document"),
    "abstract": EnvironmentDefinition("abstract"),
    "thebibliography": EnvironmentDefinition("thebibliography", num_args=1),
}

TEXT_ENVIRONMENTS = {
    "quote": EnvironmentDefinition("quote"),
    "verbatim": EnvironmentDefinition("verbatim"),
}
# Text formatting and layout environments
LAYOUT_ENVIRONMENTS = {
    "center": EnvironmentDefinition("center"),
    "spacing": EnvironmentDefinition("spacing", num_args=1),
    "minipage": EnvironmentDefinition("minipage", num_args=1),
    "multicols": EnvironmentDefinition("multicols", num_args=1),
    "adjustbox": EnvironmentDefinition("adjustbox", num_args=1),
    "adjustwidth": EnvironmentDefinition("adjustwidth", num_args=2),
    "CJK": EnvironmentDefinition("CJK", num_args=2),
}


FIGURE_ENVIRONMENTS = {
    # figures
    # assign_counter is False because captions are assigned counters
    "figure": EnvironmentDefinition(
        "figure", num_args=1, default_arg=[], assign_counter=False
    ),
    "subfigure": EnvironmentDefinition(
        "subfigure", num_args=2, default_arg=[], assign_counter=False
    ),
    "wrapfigure": EnvironmentDefinition(
        "wrapfigure", num_args=3, default_arg=[], assign_counter=False
    ),
}

TABLE_ENVIRONMENTS = {
    # tables
    # assign_counter is False because captions are assigned counters
    "table": EnvironmentDefinition(
        "table", num_args=1, default_arg=[], assign_counter=False
    ),
    "tabular": EnvironmentDefinition("tabular", num_args=1),
    "tabularx": EnvironmentDefinition("tabularx", num_args=2, has_direct_command=False),
    "tabulary": EnvironmentDefinition("tabulary", num_args=1, has_direct_command=False),
    "longtable": EnvironmentDefinition(
        "longtable", num_args=1, has_direct_command=False
    ),
}

# List environments
LIST_ENVIRONMENTS = {
    "itemize": EnvironmentDefinition("itemize"),
    "enumerate": EnvironmentDefinition("enumerate", step_counter=True),
    "description": EnvironmentDefinition("description"),
    "list": EnvironmentDefinition("list", num_args=2),
}

# Mathematical environments
MATH_ENVIRONMENTS = {
    "equation": EnvironmentDefinition("equation", step_counter=True, is_math=True),
    "align": EnvironmentDefinition(
        "align", step_counter=True, is_math=True, has_direct_command=False
    ),
    "aligned": EnvironmentDefinition("aligned", is_math=True, has_direct_command=False),
    "gather": EnvironmentDefinition(
        "gather", step_counter=True, is_math=True, has_direct_command=False
    ),
    "multline": EnvironmentDefinition(
        "multline", step_counter=True, is_math=True, has_direct_command=False
    ),
    "eqnarray": EnvironmentDefinition(
        "eqnarray", step_counter=True, is_math=True, has_direct_command=False
    ),
    "flalign": EnvironmentDefinition(
        "flalign", step_counter=True, is_math=True, has_direct_command=False
    ),
    "alignat": EnvironmentDefinition(
        "alignat", num_args=1, step_counter=True, is_math=True, has_direct_command=False
    ),
    "dmath": EnvironmentDefinition(
        "dmath", step_counter=True, is_math=True, has_direct_command=False
    ),
    "split": EnvironmentDefinition("split", is_math=True, has_direct_command=False),
    "array": EnvironmentDefinition(
        "array", num_args=1, is_math=True, has_direct_command=False
    ),
}

# # Theorem-like environments
# THEOREM_ENVIRONMENTS = {
#     "theorem": EnvironmentDefinition("theorem", step_counter=True),
#     "proof": EnvironmentDefinition("proof"),
# }

# Combine all environment dictionaries
COMMON_ENVIRONMENTS = {
    **DOCUMENT_ENVIRONMENTS,
    **TEXT_ENVIRONMENTS,
    **LAYOUT_ENVIRONMENTS,
    **FIGURE_ENVIRONMENTS,
    **TABLE_ENVIRONMENTS,
    **LIST_ENVIRONMENTS,
    **MATH_ENVIRONMENTS,
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
    env_star.step_counter = False
    env_star.assign_counter = False
    COMMON_ENVIRONMENTS[env_star.name] = env_star
