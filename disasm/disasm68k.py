#! /usr/bin/env python3
#
# Motorola 68000 Disassembler
# Copyright (c) 2019 by Jeff Tranter <tranter@pobox.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Disassembly format:
# AAAAAAAA  XX XX XX XX XX XX XX XX XX XX  MMMM.s  operands
# 00001000  4E 71                          NOP
# 00001002  60 FC                          BRA.s   $12345678
# 00001004  67 FA                          BEQ.s   $12345678
# 00001006  60 00 FF F8                    BRA.w   $12345678
# 0000107E  00 79 00 FF 00 00 12 34        ORI.w   #$FF,$1234
# 00001086  00 B9 00 00 00 FF 12 34 56 78  ORI.l   #$ff,$12345678
# 0000109E  4E F9 00 00 10 00              JMP     $DEADBEEF
#
# With --nolist option:
# MMMM.s  operands
# NOP
# BRA.s   $12345678
# BEQ.s   $12345678
# BRA.w   $12345678
# ORI.w   #$FF,$1234
# ORI.l   #$ff,$12345678
# JMP     $DEADBEEF

import argparse
import csv
import re
import sys

# Initialize variables
address = 0            # Start address if instruction
length = 0             # Length of instruction in bytes
mnemonic = ""          # Mnemonic string
sourceAddressMode = 0  # Addressing mode for source operand
destAddressMode = 0    # Addressing mode for destination operand

# Parse command line options
parser = argparse.ArgumentParser()
parser.add_argument("filename", help="Binary file to disassemble")
parser.add_argument("-n", "--nolist", help="Don't list instruction bytes (make output suitable for assembler)", action="store_true")
parser.add_argument("-a", "--address", help="Specify decimal starting address (defaults to 0)", default=0, type=int)
args = parser.parse_args()
address = args.address

# Address must be even
if address % 2:
    print("Error: Start address must be even")
    sys.exit(1)

# Open CSV file of opcodes and read into table
with open("opcodetable.csv", newline='') as csvfile:
    table = list(csv.DictReader(csvfile))

    # Do validity check on table entries and calculate bitmask and value
    # for each opcode so we can quicky test opcode for matches in the
    # table.

    for row in table:

        # Validity check: Mnemonic is not empty.
        if row["Mnemonic"] == "":
            print("Error: Empty mnemonic entry in opcode table:", row)
            sys.exit(1)

        # Validity check: B W and L are empty or the corresponding letter
        if not row["B"] in ("B", ""):
            print("Error: Bad B entry in opcode table:", row)
            sys.exit(1)
        if not row["W"] in ("W", ""):
            print("Error: Bad W entry in opcode table:", row)
            sys.exit(1)
        if not row["L"] in ("L", ""):
            print("Error: Bad L entry in opcode table:", row)
            sys.exit(1)

        # Pattern  has length 16 and each character is 0, 1, or X.
        if not re.match(r"^[01X]...............$", row["Pattern"]):
            print("Error: Bad pattern entry in opcode table:", row)
            sys.exit(1)

        # Validity check: DataSize is B, W, L, A, or empty.
        if not row["DataSize"] in ("B", "W", "L", "A", ""):
            print("Error: Bad DataSize entry in opcode table:", row)
            sys.exit(1)

        # Validity check: DataType is is I, N, D, M or empty.
        if not row["DataType"] in ("I", "N", "D", "M", ""):
            print("Error: Bad DataType entry in opcode table:", row)
            sys.exit(1)

        # Convert bit pattern to 16-bit value and bitmask, e.g.
        # pattern: 1101XXX110001XXX
        #   value: 1101000110001000
        #    mask: 1111000111111000
        # Opcode matches pattern if opcode AND mask equals value

        pattern = row["Pattern"]
        value = ""
        mask = ""

        for pos in range(16):
            if pattern[pos] in ("0", "1"):
                value += pattern[pos]
                mask += "1"
            else:
                value += "0"
                mask += "0"

        # Convert value and mask to numbers and store in table.
        row["Value"] = int(value, 2)
        row["Mask"] = int(mask, 2)

# Open input file
filename = args.filename
try:
    f = open(filename, "rb")
except FileNotFoundError:
    print(("Error: input file '{}' not found.".format(filename)), file=sys.stderr)
    sys.exit(1)

# Loop over file input
while True:

    # Get 16-bit instruction
    b1 = f.read(1)  # Get binary byte from file
    b2 = f.read(1)  # Get binary byte from file
    if len(b1) == 0:  # handle EOF
        break

    # Get op code
    opcode = ord(b1) * 256 + ord(b2)

    print("{0:04X}".format(opcode))

    # Find matching mnemonic in table
    for row in table:
        value = row["Value"]
        mask = row["Mask"]
        mnemonic = row["Mnemonic"]

        if (opcode & mask) == value:
            print("Found match for", mnemonic)
            break

# Handle instruction types - one word implicit with no operands:
# ILLEGAL, RESET, NOP, RTE, RTS, TRAPV, RTR, UNIMPLEMENTED, INVALID

# Handle instruction types - one word implicit with operands
# TRAP

# Handle instruction types - BRA

# Handle instruction types - BSR

# Handle instruction types - Bcc
