from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from latex2json.utils.tex_utils import convert_color_to_css


def define_color_handler(expander: ExpanderCore, token: Token):
    blocks = expander.parse_braced_blocks(3, expand=True)
    if len(blocks) != 3:
        expander.logger.warning("Warning: \\definecolor expects 3 arguments")
        return []

    color_name = expander.convert_tokens_to_str(blocks[0])
    model_color = expander.convert_tokens_to_str(blocks[1])
    spec = expander.convert_tokens_to_str(blocks[2])

    css_value = convert_color_to_css(model_color, spec)
    expander.state.color_registry[color_name] = css_value

    return []


def register_color_handlers(expander: ExpanderCore):
    expander.register_handler(r"\definecolor", define_color_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_color_handlers(expander)

    text = r"""
\definecolor{red}{rgb}{1,0,0}
"""
    out = expander.expand(text)
