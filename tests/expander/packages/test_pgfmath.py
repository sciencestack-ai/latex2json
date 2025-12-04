from latex2json.expander.expander import Expander


def test_pgfmathparse_basic():
    r"""Test basic \pgfmathparse and \pgfmathresult"""
    expander = Expander()
    text = r"""
    \pgfmathparse{2+3*4}
    Result: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert "Result: 14" in result


def test_pgfmathsetmacro():
    r"""Test \pgfmathsetmacro macro definition"""
    expander = Expander()
    text = r"""
    \pgfmathsetmacro{\myvalue}{10*5+7}
    The value is \myvalue
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert "The value is 57" in result


def test_pgfmath_trig_functions():
    """Test trigonometric functions in pgfmath"""
    expander = Expander()
    text = r"""
    \pgfmathparse{sin(30)+cos(60)}
    Result: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    # sin(30°) = 0.5, cos(60°) = 0.5, so result should be 1.0
    assert "Result: 1" in result


def test_pgfmath_power_and_sqrt():
    """Test power and sqrt operations"""
    expander = Expander()
    text = r"""
    \pgfmathparse{2^3 + sqrt(16)}
    Result: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    # 2^3 = 8, sqrt(16) = 4, so result should be 12
    assert "Result: 12" in result


def test_pgfmath_multiple_operations():
    """Test multiple pgfmathparse operations in sequence"""
    expander = Expander()
    text = r"""
    \pgfmathparse{5+3}
    First: \pgfmathresult
    \pgfmathparse{10*2}
    Second: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert "First: 8" in result
    assert "Second: 20" in result


def test_pgfmath_with_parentheses():
    """Test operations with parentheses"""
    expander = Expander()
    text = r"""
    \pgfmathparse{(2+3)*(4+1)}
    Result: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    # (2+3) * (4+1) = 5 * 5 = 25
    assert "Result: 25" in result


def test_pgfmath_division():
    """Test division operations"""
    expander = Expander()
    text = r"""
    \pgfmathparse{20/4}
    Result: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert "Result: 5" in result


def test_pgfmath_nested_macros():
    """Test using pgfmathsetmacro with nested references"""
    expander = Expander()
    text = r"""
    \pgfmathsetmacro{\x}{10}
    \pgfmathsetmacro{\y}{20}
    \pgfmathparse{\x+\y}
    Sum: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert "Sum: 30" in result


def test_pgfmath_floor_ceil():
    """Test floor and ceil functions"""
    expander = Expander()
    text = r"""
    \pgfmathparse{floor(3.7)}
    Floor: \pgfmathresult
    \pgfmathparse{ceil(3.2)}
    Ceil: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    assert "Floor: 3" in result
    assert "Ceil: 4" in result


def test_pgfmath_error_handling():
    """Test that errors return 0"""
    expander = Expander()
    text = r"""
    \pgfmathparse{invalid expression}
    Result: \pgfmathresult
    """
    out = expander.expand(text)
    result = expander.convert_tokens_to_str(out).strip()
    # Invalid expressions should return 0
    assert "Result: 0" in result
