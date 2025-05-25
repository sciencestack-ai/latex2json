import dataclasses
from typing import List, Optional
from latex2json.tokens.types import Token


@dataclasses.dataclass
class EnvironmentDefinition:
    name: str

    def __init__(
        self,
        name: str,
        begin_definition: List[Token] = [],
        end_definition: List[Token] = [],
        num_args: int = 0,
        default_arg: Optional[List[Token]] = None,
        step_counter: bool = False,
    ):
        self.name = name
        self.begin_definition = begin_definition
        self.end_definition = end_definition
        self.num_args = num_args
        self.default_arg = default_arg
        self.step_counter = step_counter

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
        )

    def __str__(self) -> str:
        return f"EnvironmentDefinition(name={self.name}, begin_definition={self.begin_definition}, end_definition={self.end_definition}, num_args={self.num_args}, default_arg={self.default_arg})"

    def __repr__(self) -> str:
        return self.__str__()


# Common LaTeX environments
COMMON_ENVIRONMENTS = {
    "document": EnvironmentDefinition("document"),
    "abstract": EnvironmentDefinition("abstract"),
    "figure": EnvironmentDefinition(
        "figure", num_args=1, default_arg=[]
    ),  # Optional [placement]
    "table": EnvironmentDefinition(
        "table", num_args=1, default_arg=[]
    ),  # Optional [placement]
    "itemize": EnvironmentDefinition("itemize"),
    "enumerate": EnvironmentDefinition("enumerate", step_counter=True),
    "description": EnvironmentDefinition("description"),
    "equation": EnvironmentDefinition("equation", step_counter=True),
    "align": EnvironmentDefinition("align", step_counter=True),
    "center": EnvironmentDefinition("center"),
    "verbatim": EnvironmentDefinition("verbatim"),
    "quote": EnvironmentDefinition("quote"),
    "theorem": EnvironmentDefinition("theorem", step_counter=True),
    "proof": EnvironmentDefinition("proof"),
    "tabular": EnvironmentDefinition(
        "tabular", num_args=1
    ),  # Required {cols}, no default
}
