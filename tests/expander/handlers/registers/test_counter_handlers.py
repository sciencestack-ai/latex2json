from latex2json.expander.expander import Expander


def test_basic_counter_operations():
    expander = Expander()

    # Test setcounter
    expander.expand(r"\setcounter{section}{10}")
    assert expander.state.get_counter_value("section") == 10

    # Test addtocounter
    expander.expand(r"\addtocounter{section}{5}")
    assert expander.state.get_counter_value("section") == 15

    # Test stepcounter
    expander.expand(r"\stepcounter{section}")
    assert expander.state.get_counter_value("section") == 16

    # Test refstepcounter (should behave same as stepcounter)
    expander.expand(r"\refstepcounter{section}")
    assert expander.state.get_counter_value("section") == 17

    # Test value command
    out = expander.expand(r"\value{section}")
    assert expander.convert_tokens_to_str(out) == "17"

    # test parent-child relationship and reset with stepcounter/refstepcounter
    expander.expand(r"\refstepcounter{subsection}")
    assert expander.state.get_counter_value("subsection") == 1

    expander.expand(r"\refstepcounter{section}")
    assert expander.state.get_counter_value("section") == 18
    assert expander.state.get_counter_value("subsection") == 0

    # test the
    out = expander.expand(r"\thesection")
    assert expander.convert_tokens_to_str(out) == "18"

    expander.expand(r"\stepcounter{subsection}")
    out = expander.expand(r"\thesubsection")
    assert expander.convert_tokens_to_str(out) == "18.1"


def test_new_counter():
    expander = Expander()

    # Test counter with parent
    expander.expand(r"\newcounter{mycounter}[section]")
    assert expander.state.get_counter_value("mycounter") == 0

    # Set values and verify parent-child relationship
    expander.expand(r"\setcounter{mycounter}{10}")
    assert expander.state.get_counter_value("mycounter") == 10

    # test \the<counter>
    out = expander.expand(r"\themycounter")
    assert expander.convert_tokens_to_str(out) == "10"

    # Stepping parent should reset child
    expander.expand(r"\stepcounter{section}")
    assert expander.state.get_counter_value("mycounter") == 0

    # check that it is whitespace sensitive!
    expander.expand(r"\newcounter{ mycounter2 } \setcounter{ mycounter2 }{5}")
    assert expander.state.get_counter_value(" mycounter2 ") == 5
    assert expander.state.get_counter_value(" mycounter2") is None


def test_counter_the_command():
    expander = Expander()

    # Create counter and test \the<counter> command
    expander.expand(r"\newcounter{mycounter}")
    expander.expand(r"\setcounter{mycounter}{42}")

    out = expander.expand(r"\themycounter")
    assert expander.convert_tokens_to_str(out) == "42"

    # also test with \the\value
    out = expander.expand(r"\the\value{mycounter}")
    assert expander.convert_tokens_to_str(out) == "42"


def test_counter_error_cases():
    expander = Expander()

    # Test missing counter name
    out = expander.expand(r"\setcounter{}")
    assert out == []

    # Test missing value
    out = expander.expand(r"\setcounter{mycounter}")
    assert out == []

    # Test non-existent counter in \value
    out = expander.expand(r"\value{nonexistent}")
    assert out == []


def test_counter_scope():
    expander = Expander()

    # Test that counter operations are global (not affected by scope)
    expander.push_scope()
    expander.expand(r"\setcounter{section}{10}")
    expander.pop_scope()

    assert expander.state.get_counter_value("section") == 10


def test_counter_within_without():
    expander = Expander()

    # Create test counters
    expander.expand(r"\newcounter{chapter}")
    expander.expand(r"\newcounter{figure}")

    # Test counterwithin - makes figure reset when chapter changes
    expander.expand(r"\counterwithin{figure}{chapter}")
    expander.expand(r"\setcounter{figure}{5}")
    assert expander.state.get_counter_value("figure") == 5

    # Stepping chapter should reset figure
    expander.expand(r"\stepcounter{chapter}")
    assert expander.state.get_counter_value("figure") == 0
    assert expander.state.get_counter_display("figure") == "1.0"

    # Test counterwithout - removes the dependency
    expander.expand(r"\counterwithout{figure}{chapter}")
    expander.expand(r"\setcounter{figure}{5}")

    # Now stepping chapter should not reset figure
    expander.expand(r"\stepcounter{chapter}")
    assert expander.state.get_counter_value("figure") == 5
    assert expander.state.get_counter_display("figure") == "5"

    # Test the representation format after counterwithin
    expander.expand(r"\counterwithin{figure}{chapter}")
    expander.expand(r"\setcounter{chapter}{2}")
    expander.expand(r"\setcounter{figure}{3}")

    out = expander.expand(r"\thefigure")
    assert expander.convert_tokens_to_str(out) == "2.3"  # Should show as chapter.figure

    # counterwithin has unique property that even if the parent is zero, it will have the parent displayed!
    expander.expand(r"\setcounter{chapter}{0}")
    out = expander.expand(r"\thefigure")
    assert expander.convert_tokens_to_str(out) == "0.3"


def test_direct_counter_setting():
    text = r"""
    \makeatletter
\c@section 3 % set section counter as 3
\the\value{section} % 3
"""

    expander = Expander()
    out = expander.expand(text)
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "3"

    # check that it is also a register macro type that can be used with e.g. \ifodd
    out = expander.expand(r"\ifodd\c@section ODD \else EVEN \fi")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "ODD"

    # set it as even
    expander.expand(r"\c@section 4")
    out = expander.expand(r"\ifodd\c@section ODD \else EVEN \fi")
    out_str = expander.convert_tokens_to_str(out).strip()
    assert out_str == "EVEN"
