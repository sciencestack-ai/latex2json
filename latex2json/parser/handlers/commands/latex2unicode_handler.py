from typing import List
from latex2json.tokens.types import Token, TokenType
from latex2json.nodes.base_nodes import CommandNode, TextNode
from latex2json.parser.parser_core import Handler, ParserCore

from latex2json.latex_maps.latex2unicode import latex2unicode


def make_latex2unicode_handler(unicode_value: str | int) -> Handler:
    char = chr(unicode_value) if isinstance(unicode_value, int) else unicode_value

    def handler(parser: ParserCore, token: Token):
        return [TextNode(char)]

    return handler


def unicode_handler(parser: ParserCore, token: Token):
    # UNICODE_PATTERN = r"\\u([0-9a-fA-F]{4,6})"
    # check next tokens for unicode sequence
    pattern_tokens: List[Token] = []
    tok = parser.peek()
    while tok and tok.type == TokenType.CHARACTER and len(pattern_tokens) < 6:
        if tok.value.isalnum():
            parser.consume()
            pattern_tokens.append(tok)
        else:
            break
        tok = parser.peek()

    if 4 <= len(pattern_tokens) <= 6:
        char = ""
        try:
            char = chr(int("".join(tok.value for tok in pattern_tokens), 16))
        except (ValueError, IndexError):
            return []
        return [TextNode(char)]

    # push back pattern tokens to stream if malformed unicode sequence
    parser.push_tokens(pattern_tokens)
    return [CommandNode(token.value)]


def register_latex2unicode_handler(parser: ParserCore):
    for command, unicode_value in latex2unicode.items():
        parser.register_handler(
            command,
            make_latex2unicode_handler(unicode_value),
            text_mode_only=True,
        )

    # NOTE: LaTeX's \u is purely an accent command, not a Unicode escape mechanism. So we disable it
    # parser.register_handler("\\u", unicode_handler)


if __name__ == "__main__":
    # from latex2json.parser import Parser

    # parser = Parser()
    # text = r"""
    # \star \u00a7 \sqrt{}
    # """.strip()
    # # tokens = parser.expander.expand(text)
    # out = parser.parse(text)

    for command, unicode_value in latex2unicode.items():
        command = command.lstrip("\\")
        if not command.isalpha():
            continue
        # if "{" in command or "\\" in command:
        #     continue
        print('"%s": %d,' % (command, unicode_value))
