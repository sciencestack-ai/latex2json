from latex2json.expander.expander import Expander


def test_for_loop_handler():
    expander = Expander()

    text = r"""
\newcounter{x}
\forloop{x}{1}{\value{x} < 10}{ % value of x is 1...9
    \arabic{x}                  % print x in arabic notation
}
"""

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    sequence = out_str.split("\n")
    sequence = [s.strip() for s in sequence if s.strip()]
    assert sequence == ["%d" % i for i in range(1, 10)]


def test_nested_for_loop():
    expander = Expander()
    # nested forloop
    text = r"""
    \newcounter{x}                     % define two counters
    \newcounter{y}
    \forloop{y}{0}{\value{y} < 5}{     % y goes from 0 to 4
        \forloop{x}{0}{\value{x} < 3}{ % x goes from 0 to 2
            (\arabic{x},\arabic{y})     % print out tuples
        }
    }
"""

    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out)
    sequence = out_str.split("\n")
    sequence = [s.strip() for s in sequence if s.strip()]

    expected = []
    for y in range(5):
        for x in range(3):
            expected.append(f"({x},{y})")
    assert sequence == expected


def test_at_for_loop_handler():
    expander = Expander()

    # equivalent to \@for \var := {a,b,c} \do {[\var]}
    text = r"""
    \makeatletter
    \@forloop a,b,c,\@nil, \@nil \@@\myvar{[\myvar] }
""".strip()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == r"[a] [b] [c]"
