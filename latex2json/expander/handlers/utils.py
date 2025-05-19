from typing import List

from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.types import Token, TokenType


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
