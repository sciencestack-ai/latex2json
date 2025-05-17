from typing import List
from latex2json.nodes.base import ASTNode, check_asts_equal


class EnvironmentNode(ASTNode):
    def __init__(
        self,
        name: str,
        opt_args: List[ASTNode],
        args: List[ASTNode],
        body: List[ASTNode],
    ):
        self.name = name
        self.opt_args = opt_args
        self.args = args
        self.body = body

        # strip_whitespace(self.body)

        self.set_children(self.opt_args + self.args + self.body)

    def __str__(self):
        return f"Environment: {self.name} [{self.opt_args}]\n{self.body}\nEND Environment: {self.name}"

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: ASTNode):
        if not isinstance(other, EnvironmentNode):
            return False
        same = self.name == other.name
        if not same:
            return False
        return (
            check_asts_equal(self.body, other.body)
            and check_asts_equal(self.args, other.args)
            and check_asts_equal(self.opt_args, other.opt_args)
        )
