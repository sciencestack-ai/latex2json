from typing import List
from latex2json.nodes import (
    ASTNode,
    ArgNode,
    TextNode,
)
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType
from latex2json.tokens.utils import is_integer_token

# from copy import deepcopy


def substitute_args(
    definition: List[ASTNode],
    args: List[ASTNode],
    depth: int = 1,
    math_mode: bool = False,
) -> List[ASTNode]:
    for i, node in enumerate(definition):
        if isinstance(node, ArgNode):
            if node.depth == depth:
                index = node.num - 1  # convert to 0-based index
                if index < len(args):
                    node.value = [args[index]]
        elif node.children:
            substitute_args(node.children, args, depth=depth, math_mode=math_mode)
    return extract_nodes(definition)


# Move these into a class to handle state
class TokenArgBufferState:
    def __init__(self):
        self.params_buffer: List[Token] = []
        self.number_buffer: List[Token] = []

    def parse_buffer_with_args(
        self, args: List[List[Token]], depth: int, math_mode=False
    ):
        # return the buffer as is by default
        subbed: List[Token] = self.params_buffer + self.number_buffer

        if self.params_buffer and self.number_buffer:
            num_params = len(self.params_buffer)
            num_value = int("".join(t.value for t in self.number_buffer))
            arg_depth = ArgNode.compute_depth(num_params)
            if arg_depth == depth and num_value <= len(args):
                subbed = args[num_value - 1]

        # flush buffers
        self.params_buffer = []
        self.number_buffer = []
        return subbed


def extract_nodes(nodes: List[ASTNode]) -> List[ASTNode]:
    out = []
    for node in nodes:
        # if isinstance(node, BraceNode) or isinstance(node, BracketNode):
        #     out.extend(extract_nodes(node.children))
        if isinstance(node, ArgNode):
            out.extend(extract_nodes(node.value))
        elif isinstance(node, List):
            out.extend(extract_nodes(node))
        else:
            out.append(node)
    return out


def substitute_token_args(
    definition: List[Token],
    args: List[List[Token]],
    math_mode: bool = False,
) -> List[Token]:

    out: List[Token] = []

    for token in definition:
        if token.type == TokenType.PARAMETER:
            index = int(token.value) - 1
            if index < len(args):
                out.extend(args[index])
        else:
            out.append(token)

    # buffer_state = TokenArgBufferState()

    # def parse_buffer():
    #     out.extend(
    #         buffer_state.parse_buffer_with_args(args, depth, math_mode=math_mode)
    #     )

    # for token in definition:
    #     if token.catcode == Catcode.PARAMETER:
    #         if buffer_state.number_buffer:
    #             parse_buffer()
    #         buffer_state.params_buffer.append(token)
    #     elif is_integer_token(token):
    #         if buffer_state.params_buffer:
    #             if buffer_state.number_buffer:
    #                 parse_buffer()
    #                 out.append(token)
    #             else:
    #                 buffer_state.number_buffer.append(token)
    #         else:
    #             out.append(token)
    #     else:
    #         parse_buffer()
    #         out.append(token)
    # parse_buffer()
    return out


if __name__ == "__main__":
    # argnode1 = ArgNode(1, 1)
    # argnode2 = ArgNode(2, 1)
    # argnode_1_2 = ArgNode(1, 2)

    # # e.g. #1 x #2 = ##1
    # definition: List[ASTNode] = [
    #     argnode1,
    #     TextNode(" x "),
    #     argnode2,
    #     TextNode(" = "),
    #     argnode_1_2,
    # ]

    # depth1_args = [TextNode("100"), TextNode("2")]
    # depth2_args = [TextNode("200")]
    # substituted = substitute_args(definition, depth2_args, depth=argnode_1_2.depth)
    # print(substituted)

    # suppose definition ie e.g. "a b # 1 #1 #2##1"
    definition = [
        Token(TokenType.CHARACTER, "a", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "b", catcode=Catcode.LETTER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "#", catcode=Catcode.PARAMETER),
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
    ]

    # and we want to sub #1 and #2 with "123" and "4 5 6"
    arg1 = [
        Token(TokenType.CHARACTER, "1", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "2", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, "3", catcode=Catcode.OTHER),
    ]
    arg2 = [
        Token(TokenType.CHARACTER, "4", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "5", catcode=Catcode.OTHER),
        Token(TokenType.CHARACTER, " ", catcode=Catcode.SPACE),
        Token(TokenType.CHARACTER, "6", catcode=Catcode.OTHER),
    ]
    args = [arg1, arg2]
    substituted = substitute_token_args(
        definition, args, depth=ArgNode.compute_depth(num_params=1)
    )
