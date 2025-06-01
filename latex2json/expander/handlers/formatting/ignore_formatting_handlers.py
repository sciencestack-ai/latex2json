from latex2json.expander.expander_core import ExpanderCore
from latex2json.tokens.types import Token
from typing import Optional

ignored_formatting_pattern_N_blocks = {
    # Float-related formatting
    "floatname": 2,
    "floatstyle": 1,
    "restylefloat": 1,
    # Section-related formatting
    "titleformat": 4,
    "titlespacing": 4,
    "sectionformat": 1,
    # Page-related formatting
    "pagestyle": 1,
    "thispagestyle": 1,
    # Font-related formatting
    "setmainfont": 1,
    "setsansfont": 1,
    "setmonofont": 1,
    # Package processing
    "ProcessOptions": 0,  # Actually takes no arguments
    # You might also add:
    "geometry": 1,  # \geometry{margin=1in}
    "setstretch": 1,  # \setstretch{1.5} - line spacing
    "color": 1,  # \color{red}
}


def make_formatting_ignore_handler(pattern: str, n_blocks: int):
    def ignore_handler(expander: ExpanderCore, token: Token) -> Optional[list[Token]]:
        blocks = expander.parse_braced_blocks(n_blocks)
        return []

    return ignore_handler


def register_ignore_format_handlers(expander: ExpanderCore):
    """Register all formatting-related command handlers"""
    for command, n_blocks in ignored_formatting_pattern_N_blocks.items():
        expander.register_handler(
            command,
            make_formatting_ignore_handler(command, n_blocks),
            is_global=True,
        )


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ignore_format_handlers(expander)

    # Test some formatting commands
    out1 = expander.expand(r"\floatname{figure}{Fig.}")
    out2 = expander.expand(r"\pagestyle{fancy}")
    out3 = expander.expand(
        r"\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}"
    )
