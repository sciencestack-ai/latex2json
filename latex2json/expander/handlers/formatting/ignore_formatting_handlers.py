from latex2json.expander.expander_core import ExpanderCore
from latex2json.expander.handlers.handler_utils import register_ignore_handlers_util

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
    # "color": 1,  # \color{red}
}


def register_ignore_format_handlers(expander: ExpanderCore):
    """Register all formatting-related command handlers"""
    register_ignore_handlers_util(expander, ignored_formatting_pattern_N_blocks)


if __name__ == "__main__":
    from latex2json.expander.expander import Expander

    expander = Expander()
    register_ignore_handlers_util(expander)

    # Test some formatting commands
    out1 = expander.expand(r"\floatname{figure}{Fig.}")
    out2 = expander.expand(r"\pagestyle{fancy}")
    out3 = expander.expand(
        r"\titleformat{\section}{\normalfont\Large\bfseries}{\thesection}{1em}{}"
    )
