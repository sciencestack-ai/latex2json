from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from latex2json.utils.tex_utils import convert_color_to_css


def define_color_handler(expander: ExpanderCore, token: Token):
    expander.skip_whitespace()
    namespace = expander.parse_bracket_as_tokens()
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(3, expand=True)
    if len(blocks) != 3:
        expander.logger.warning("\\definecolor expects 3 arguments")
        return []

    color_name = expander.convert_tokens_to_str(blocks[0])
    model_color = expander.convert_tokens_to_str(blocks[1])
    spec = expander.convert_tokens_to_str(blocks[2])

    css_value = convert_color_to_css(model_color, spec)
    expander.state.color_registry[color_name] = css_value

    return []


def colorlet_handler(expander: ExpanderCore, token: Token):
    r"""
    \colorlet{name}{color_expr}
    Defines a new color as an alias or modification of an existing one.
    Supports simple aliasing (e.g. \colorlet{foo}{red}) and
    mixing expressions (e.g. \colorlet{foo}{red!50!blue}).
    """
    expander.skip_whitespace()
    blocks = expander.parse_braced_blocks(2, expand=True)
    if len(blocks) != 2:
        expander.logger.warning("\\colorlet expects 2 arguments")
        return []

    new_name = expander.convert_tokens_to_str(blocks[0]).strip()
    color_expr = expander.convert_tokens_to_str(blocks[1]).strip()

    # Try to resolve from the color registry first (simple alias)
    if color_expr in expander.state.color_registry:
        expander.state.color_registry[new_name] = expander.state.color_registry[
            color_expr
        ]
    else:
        # Store the expression as-is — downstream can resolve it or use it as a CSS name
        expander.state.color_registry[new_name] = color_expr

    return []


def register_color_handlers(expander: ExpanderCore):
    expander.register_handler(r"\definecolor", define_color_handler, is_global=True)
    expander.register_handler(r"\colorlet", colorlet_handler, is_global=True)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_color_handlers(expander)

    text = r"""
\definecolor{red}{rgb}{1,0,0}
"""
    out = expander.expand(text)
