# assign arbitrary numbers to inserts (Tex generally assigns 255 and decreasing, but we're not bound by that)

BUILTIN_INSERTS = [
    # Plain TeX core
    "footins",  # main page footnotes
    # LaTeX kernel
    "@mpfootins",  # minipage/parbox footnotes
    "@kludgeins",  # used internally for marginpars
    "@topins",  # floats at top of page
    "@botins",  # floats at bottom of page
    "@deferlist",  # deferred floats (stored until later)
    # Note: float handling actually creates multiple insertion slots
    # but these are the canonical names in the kernel
]
