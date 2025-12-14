from typing import List
from latex2json.expander.expander_core import ExpanderCore
from latex2json.latex_maps.url_commands import URL_COMMANDS
from latex2json.tokens import Token
from latex2json.tokens.catcodes import Catcode
from latex2json.tokens.utils import wrap_tokens_in_braces, wrap_tokens_in_brackets


def make_url_handler(parse_title: bool = False):
    def handler(expander: ExpanderCore, token: Token):
        expander.skip_whitespace()
        title = []
        if parse_title:
            title = expander.parse_bracket_as_tokens(expand=True) or []
            if title:
                title = wrap_tokens_in_brackets(title)
            expander.skip_whitespace()
        # parse urls as verbatim! so that e.g. % is valid and not treated as comment
        output = expander.parse_brace_as_tokens(verbatim=True, expand=False) or []
        if output:
            # convert all to letter
            for tok in output:
                tok.catcode = Catcode.LETTER
            output = wrap_tokens_in_braces(output)
        return [token] + title + output

    return handler


def register_url_handlers(expander: ExpanderCore):
    for url_command, spec in URL_COMMANDS.items():
        expander.register_handler(
            url_command,
            make_url_handler(parse_title=spec.startswith("[")),
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    out = expander.expand(r"\url{https://www.google.com/%sdsd%33}")
    out_str = expander.convert_tokens_to_str(out)
    print(out_str)
