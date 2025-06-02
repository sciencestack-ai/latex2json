from latex2json.expander.expander import Expander


def test_hvskip_handlers():
    expander = Expander()

    # Test horizontal skip commands
    out = expander.expand(r"\hskip 10pt")
    assert out == []

    out = expander.expand(r"\hskip 2em plus 1fil")
    assert out == []

    # Test vertical skip commands
    out = expander.expand(r"\vskip 20pt")
    assert out == []

    out = expander.expand(r"\vskip 1in plus 2pt minus 3pt")
    assert out == []


def test_ignored_skip_commands():
    expander = Expander()

    # Test basic skips
    skips = [r"\smallskip", r"\medskip", r"\bigskip"]
    for skip in skips:
        out = expander.expand(skip)
        assert out == []

    # Test horizontal fills
    h_fills = [r"\hfil", r"\hfill", r"\hfilneg", r"\hss"]
    for fill in h_fills:
        out = expander.expand(fill)
        assert out == []

    # Test vertical fills
    v_fills = [r"\vfil", r"\vfill", r"\vfilneg", r"\vss"]
    for fill in v_fills:
        out = expander.expand(fill)
        assert out == []
