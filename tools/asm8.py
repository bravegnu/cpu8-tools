"""Assembler for an 8-bit CPU described in

https://minnie.tuhs.org/CompArch/Tutes/week03.html
"""

from enum import IntEnum

import re
import sys

MNEMONIC_LIST = ("AND OR ADD SUB LW SW MOV NOP "
                 "JEQ JNE JGT JLT LWI SWI LI JMP "
                 "BYTE").split()

REG_LIST = "R0 R1 R2 R3".split()

SYNTAX = re.compile(r"^((?P<label>\w+):)?"
                    r"(\s*(?P<mnemonic>.?\w+)"
                    r"(\s+(?P<operand1>\w+)\s*"
                    r"(,\s*\(?(?P<operand2>\w+)\)?)?)?)?"
                    r"\s*([;#].*)?$")

Mnemonics = IntEnum("Mnemonics", zip(MNEMONIC_LIST, range(17)))


def error(msg):
    """Prints an error message and exits."""

    print("asm8: {}".format(msg))
    exit(1)


def parse_reg(reg_name, line):
    """Returns the register index.

    Exits with error message if the register is invalid.
    """
    try:
        return REG_LIST.index(reg_name)
    except ValueError:
        error("invalid register {} in line {}".format(reg_name, line))


def parse_mnemonic(mnemonic, line):
    """Returns the opcode corresponding to the mnemoic.

    Exits with an error message if the mnemonic is invalid.
    """
    if mnemonic.startswith("."):
        mnemonic = mnemonic[1:]

    try:
        mnemonic = mnemonic.upper()
        return Mnemonics[mnemonic]
    except KeyError:
        error("invalid mnemonic {} in line {}".format(mnemonic, line))


def has_imm(opcode):
    """Returns True if the opcode has an immediate operand."""

    return bool(opcode & 0b1000)


def mk_inst(opcode, dreg, sreg, imm):
    """Returns the bytes corresponding to the parsed instruction."""

    inst = []
    if opcode == Mnemonics.BYTE:
        inst.append(imm)
    else:
        inst.append(opcode << 4 | dreg << 2 | sreg)
        if has_imm(opcode):
            inst.append(imm)

    return bytes(inst)


def parse_imm(imm, symtab, line):
    """Parses immediate value, could be an integer or a label."""

    try:
        imm = int(imm, 0)
        if imm > 255:
            error("invalid immediate value {} in line {}".format(imm, line))
    except ValueError:
        try:
            imm = symtab[imm]
        except KeyError:
            error("invalid label {} in line {}".format(imm, line))

    return imm


def pass_one(prog, start_addr):
    """Returns the symbol table for the program."""
    symtab = {}
    next_addr = start_addr

    for i, line in enumerate(prog):
        addr = next_addr
        m = SYNTAX.match(line)
        if not m:
            error("parse error in line {}".format(i))

        label = m.group("label")
        mnemonic = m.group("mnemonic")

        if label is not None:
            symtab[label] = addr

        if mnemonic is None:
            continue

        opcode = parse_mnemonic(mnemonic, i)

        if has_imm(opcode):
            next_addr += 2
        else:
            next_addr += 1

    return symtab


def pass_two(prog, symtab):
    """Parses the asm program and generate binary file."""
    byte_list = []

    for i, line in enumerate(prog):
        m = SYNTAX.match(line)
        mnemonic = m.group("mnemonic")
        operand1 = m.group("operand1")
        operand2 = m.group("operand2")

        if mnemonic is None:
            continue

        opcode = 0
        dreg = 0
        sreg = 0
        imm = None

        opcode = parse_mnemonic(mnemonic, i)

        if operand1 is not None:
            if opcode == Mnemonics.JMP or opcode == Mnemonics.BYTE:
                imm = parse_imm(operand1, symtab, i)
            else:
                operand1 = operand1.upper()
                dreg = parse_reg(operand1, i)

        if operand2 is not None:
            if has_imm(opcode):
                imm = parse_imm(operand2, symtab, i)
            else:
                operand2 = operand2.upper()
                sreg = parse_reg(operand2, i)

        inst = mk_inst(opcode, dreg, sreg, imm)
        byte_list.append(inst)

    return b"".join(byte_list)


def assemble(lines):
    """Returns the assembled bytes for give source."""
    symtab = pass_one(lines, 0)
    return pass_two(lines, symtab)


def main(prog_filename, bin_filename):
    """Main application entry point."""

    try:
        with open(bin_filename, "wb") as bin_file:
            with open(prog_filename, "r") as prog_file:
                lines = prog_file.readlines()
                binary = assemble(lines)
                bin_file.write(binary)
    except OSError as exc:
        error("error opening file: {}".format(exc))

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: asm8 <asm-file> <bin-file>")
        exit(1)

    main(sys.argv[1], sys.argv[2])
