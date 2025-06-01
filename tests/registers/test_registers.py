import pytest

from latex2json.registers import (
    RegisterType,
    TexRegisters,
    Box,
)


def test_count_register():
    registers = TexRegisters()

    # Test numeric register
    registers.set_register(RegisterType.COUNT, 5, 42)
    assert registers.get_register_value(RegisterType.COUNT, 5) == 42

    # Test named register
    registers.set_register(RegisterType.COUNT, "mycounter", 100)
    assert registers.get_register_value(RegisterType.COUNT, "mycounter") == 100


def test_dimen_register():
    registers = TexRegisters()

    # Test numeric register (dimensions in scaled points)
    registers.set_register(RegisterType.DIMEN, 1, 65536)  # 1pt = 65536sp
    assert registers.get_register_value(RegisterType.DIMEN, 1) == 65536

    # Test named register
    registers.set_register(RegisterType.DIMEN, "mywidth", 32768)
    assert registers.get_register_value(RegisterType.DIMEN, "mywidth") == 32768


def test_skip_register():
    registers = TexRegisters()

    registers.set_register(RegisterType.SKIP, "myskip", 100)

    result = registers.get_register_value(RegisterType.SKIP, "myskip")
    assert result == 100


def test_delete_register():
    registers = TexRegisters()

    # Set and then delete a named register
    registers.set_register(RegisterType.COUNT, "temp", 42)
    assert registers.get_register_value(RegisterType.COUNT, "temp") == 42

    registers.delete_register(RegisterType.COUNT, "temp")
    assert registers.get_register_value(RegisterType.COUNT, "temp") is None


def test_invalid_register_access():
    registers = TexRegisters()

    # Test out of bounds numeric register
    assert registers.get_register_value(RegisterType.COUNT, 300) is None

    # Test non-existent named register
    assert registers.get_register_value(RegisterType.COUNT, "nonexistent") is None
