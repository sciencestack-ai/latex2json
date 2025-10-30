from latex2json.parser.parser_core import MacroPattern, ParserCore


def register_patterns_to_ignore(parser: ParserCore):
    # ignore unknown IEEE commands
    IEEE_pattern = MacroPattern(
        name_predicate=lambda name: name.startswith("IEEE"),
        handler=lambda parser, token: [],
    )
    parser.register_macro_pattern(IEEE_pattern)


if __name__ == "__main__":
    from latex2json.parser.parser import Parser

    parser = Parser()
    register_patterns_to_ignore(parser)

    text = r"""
    \IEEEabstract
    \IEEEmembership
    """.strip()
    nodes = parser.parse(text)
    print(nodes)
