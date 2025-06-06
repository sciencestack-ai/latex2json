from typing import List
from latex2json.expander.expander_core import ExpanderCore, is_relax_token
from latex2json.tokens.types import Token, TokenType

import colorsys


def convert_color_to_css(model: str, spec: str) -> str:
    """Convert LaTeX color specifications to CSS values"""

    if model == "rgb":
        # LaTeX: rgb values 0-1 → CSS: rgb values 0-255
        # Input: "0.2, 0.4, 0.8"
        values = [float(x.strip()) for x in spec.split(",")]
        rgb_values = [int(round(v * 255)) for v in values]
        return f"rgb({rgb_values[0]}, {rgb_values[1]}, {rgb_values[2]})"

    elif model == "RGB":
        # LaTeX: RGB values 0-255 → CSS: same
        # Input: "255, 100, 50"
        values = [int(x.strip()) for x in spec.split(",")]
        return f"rgb({values[0]}, {values[1]}, {values[2]})"

    elif model == "HTML":
        # LaTeX: hex without # → CSS: hex with #
        # Input: "FF6432" or "2E8B57"
        hex_value = spec.strip().upper()
        return f"#{hex_value}"

    elif model.lower() == "cmyk":
        # LaTeX: CMYK 0-1 values → CSS: convert to RGB
        # Input: "0.5, 0.8, 0, 0.2"
        values = [float(x.strip()) for x in spec.split(",")]
        c, m, y, k = values

        # CMYK to RGB conversion
        r = int(255 * (1 - c) * (1 - k))
        g = int(255 * (1 - m) * (1 - k))
        b = int(255 * (1 - y) * (1 - k))

        return f"rgb({r}, {g}, {b})"

    elif model == "gray" or model == "grey":
        # LaTeX: gray value 0-1 → CSS: same value for R, G, B
        # Input: "0.7"
        gray_value = float(spec.strip())
        rgb_value = int(round(gray_value * 255))
        return f"rgb({rgb_value}, {rgb_value}, {rgb_value})"

    elif model == "hsb":
        # LaTeX: HSB values → CSS: convert to RGB
        # Input: "0.6, 0.8, 0.9" (hue, saturation, brightness)

        values = [float(x.strip()) for x in spec.split(",")]
        h, s, b = values

        # HSB to RGB (note: colorsys uses HSV which is same as HSB)
        r, g, b = colorsys.hsv_to_rgb(h, s, b)
        rgb_values = [int(round(c * 255)) for c in (r, g, b)]

        return f"rgb({rgb_values[0]}, {rgb_values[1]}, {rgb_values[2]})"

    else:
        # Unknown model - return a fallback
        return "black"


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
