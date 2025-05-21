├── primitives/
│   ├── __init__.py
│   │
│   ├── registers/
│   │   ├── __init__.py
│   │   ├── count_handlers.py    # For \count, \the\count, \newcount, \advance, \multiply, \divide (on counts)
│   │   ├── dimen_handlers.py    # For \dimen, \the\dimen, \newdimen, \advance, \multiply, \divide (on dimen)
│   │   ├── skip_handlers.py     # For \skip, \the\skip, \newskip, etc.
│   │   ├── toks_handlers.py     # For \toks, \the\toks, \newtoks, etc.
│   │   ├── box_handlers.py      # For \box, \copy, \setbox, \newbox, \unhbox, \unvbox etc.
│   │   └── muskip_handlers.py   # For \muskip, \the\muskip, \newmuskip, etc.
│   │
│   ├── conditionals/             # Or keep your 'if_else' if it covers all \if...
│   │   ├── __init__.py
│   │   ├── if_num_handlers.py    # For \ifnum, \ifdim, \ifodd
│   │   ├── if_token_handlers.py  # For \ifx, \ifeof, \iftrue, \iffalse
│   │   └── if_mode_handlers.py   # For \ifhmode, \ifvmode, \ifmmode, \ifinner
│   │
│   ├── definitions/
│   │   ├── __init__.py
│   │   ├── macro_def_handlers.py # For \def, \edef, \gdef, \xdef, \let
│   │   └── chardef_handlers.py   # For \chardef, \mathchardef, \countdef, \dimendef, \skipdef, \toksdef
│   │
│   ├── modes/
│   │   ├── __init__.py
│   │   ├── horizontal_mode_handlers.py # For \hbox, \hfil, \hskip, \hglue etc.
│   │   ├── vertical_mode_handlers.py   # For \vbox, \vfil, \vskip, \vglue, \par, \indent, \noindent etc.
│   │   └── math_mode_handlers.py       # For entering/exiting math mode
│   │
│   ├── fonts/
│   │   ├── __init__.py
│   │   └── font_selection_handlers.py  # For \font, \selectfont, \fam etc.
│   │
│   └── misc_primitives/
│       ├── __init__.py
│       ├── expansion_control_handlers.py # For \expandafter, \noexpand, \csname, \string
│       ├── input_output_handlers.py      # For \input, \openout, \closeout, \read, \write, \message, \errmessage
│       └── termination_handlers.py       # For \relax, \end, \dump
│