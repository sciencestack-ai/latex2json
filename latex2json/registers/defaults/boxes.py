BASE_BOXES = [
    "hbox",
    "vbox",
    "vtop",
]

ADVANCED_BOX_SPECS = {
    "fbox": "{",  # \fbox{text}
    "boxed": "{",  # \boxed{text}
    "parbox": "[[[{{",  # \parbox[pos][height][inner-pos]{width}{text}
    "makebox": "[[{",  # \makebox[width]{text}
    "framebox": "[[{",  # \framebox[width][pos]{text}
    "raisebox": "{[[{",  # \raisebox{distance}[extend-above][extend-below]{text}
    "colorbox": "{{",  # \colorbox{color}{text}
    "fcolorbox": "{{{",  # \fcolorbox{border}{bg}{text}
    "scalebox": "{{",  # \scalebox{scale}{text}
    "mbox": "{",  # \mbox{text}, strip out all EOL
    "pbox": "{{",  # \pbox{x}{text}
    "resizebox": "{{{",  # \resizebox{width}{height}{text}
    "rotatebox": "{{",  # \rotatebox{angle}{text}
    "adjustbox": "{{",  # \adjustbox{max width=\textwidth}{text}
    "tcbox": "[{",  # \tcbox[options]{text}
    # llap rlap clap
    "llap": "{",
    "rlap": "{",
    "clap": "{",
    "strutbox": "{",
    "tcbox": "[{",  # \tcbox[options]{text}
}

KATEX_SUPPORTED_BOXES = [
    "hbox",
    "fbox",
    "raisebox",
    "colorbox",
    "fcolorbox",
]
