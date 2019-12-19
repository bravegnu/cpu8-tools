import pytest

from unittest.mock import Mock
from io import BytesIO
from io import StringIO

from asm8 import assemble
from asm8 import main as asm8_main


test_valid_insts = [
    ("AND R0, R0",           b"\x00"),         # Single Byte Instruction
    ("JMP 0x00",             b"\xF0\x00"),     # Two Byte Instruction
    ("SW R1, (R1)",          b"\x55"),         # Indirect Addressing
    ("",                     b""),             # No instructions
    ("label:",               b""),             # Only label
    ("nop",                  b"\x70"),         # Lower case instruction
    ("t: jmp t",             b"\xF0\x00"),     # Jump to self
    ("# Comment",            b""),             # Only comment
    ("label: # Comment",     b""),             # Only label and comment
    ("label: NOP # Comment", b"\x70"),         # Label Mnemonic and Comment
    ("NOP\n" * 3,            b"\x70\x70\x70"), # Instruction sequence
    ("b: NOP\njmp b",        b"\x70\xF0\x00"), # Jump Backward
    ("jmp f\nf: NOP",        b"\xF0\x02\x70"), # Jump Forward
    ("LWI R1, 0x01",         b"\xC4\x01"),     # Immediate second operand
    ("LWI R1, 10",           b"\xC4\x0A"),     # Immediate in decimal format
    ("LWI R1, 0b01010101",   b"\xC4\x55"),     # Immediate in binary format
    (".byte 0x00",           b"\x00"),         # Pseudo instruction
    (".byte 0xAA",           b"\xAA"),         # Non-zero value
]


@pytest.mark.parametrize("inst,expected_bin", test_valid_insts)
def test_valid_assemble(inst, expected_bin):
    got_bin = assemble(inst.split("\n"))
    
    assert got_bin == expected_bin


test_invalid_insts = [
    ("XYZ",            "invalid mnemonic"),
    ("jmp label",      "invalid label"),
    ("ADD R4, R4",     "invalid register"),
    ("LWI R0, 0xFFFF", "invalid immediate"),
    ("!",              "parse error"),
]


@pytest.mark.parametrize("inst,error_msg", test_invalid_insts)
def test_invalid_assemble(inst, error_msg, capfd):
    with pytest.raises(SystemExit):
        assemble(inst.split("\n"))

    out, err = capfd.readouterr()
    assert error_msg in out


class XBytesIO(BytesIO):
    def close(self):
        self.value_at_close = self.getvalue()
        super().close()


@pytest.fixture
def bin_file(monkeypatch):
    import builtins

    bin_file = XBytesIO()
    asm_file = StringIO("nop")
    img_file = StringIO()
    mock_open = Mock(side_effect=[asm_file, bin_file, img_file])
    monkeypatch.setattr(builtins, "open", mock_open)

    return bin_file


def test_main(bin_file):
    asm8_main("hello.s")

    assert bin_file.value_at_close == b"\x70"
