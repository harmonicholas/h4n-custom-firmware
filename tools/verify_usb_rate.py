#!/usr/bin/env python3
"""Bounded execution of the released USB rate hook; requires a local image."""
import argparse
import json
from pathlib import Path
from patch_firmware import parse, file_offset, sha
ROOT = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser(description=__doc__)
p.add_argument('image', type=Path)
args = p.parse_args()
image = args.image.read_bytes()
release = json.loads((ROOT / 'patches/1.9C.json').read_text())
assert sha(image) in {v['sha256'] for v in release['targets'].values()}, 'Not a current release image'
manifest = json.loads((ROOT / 'patches/usb-rate-labels.json').read_text())
sections, _ = parse(image)
assert int.from_bytes(image[252:256], 'big') == sum(image[256:]) & 0xffffffff

def descriptors(raw):
    position = 0
    result = []
    while position < len(raw):
        length = raw[position]
        assert length >= 2 and position + length <= len(raw)
        result.append(raw[position:position + length])
        position += length
    assert position == len(raw)
    return result

def read(address, count):
    offset = file_offset(sections, address)
    return image[offset:offset + count]


BASE = 0x6d99a0
initial = read(BASE * 2, 348)[1::2]
memory = {BASE + i: value for i, value in enumerate(initial)}
cases = []
for selection in [0, 1, 0, 1, 1, 0] * 8:
    memory[manifest['selection']] = selection
    registers = {i: 0x100 + i for i in range(16)}
    original_registers = registers.copy()
    pc = manifest['hook']
    writes = []
    for steps in range(100):
        if pc == manifest['resume']:
            break
        instruction = read(pc, 8)
        if instruction[0] == 0x6a:
            pc = int.from_bytes(instruction[1:4], 'big')
            continue
        if instruction[:2] == bytes.fromhex('6d10'):
            pc += 4 + (int.from_bytes(instruction[2:4], 'big', signed=True) if registers[0] != 0 else 0)
            continue
        if instruction[0] == 0x76 and instruction[3] in (0x98, 0xa8):
            registers[instruction[3] >> 4] = int.from_bytes(instruction[1:3], 'big')
            pc += 4
            continue
        if instruction[:2] == bytes.fromhex('a031'):
            address = int.from_bytes(instruction[2:5], 'big')
            assert address == manifest['selection']
            registers[0] = memory[address]
            pc += 5
            continue
        if instruction[:2] in (bytes.fromhex('c931'), bytes.fromhex('ca31')):
            address = int.from_bytes(instruction[2:5], 'big')
            memory[address] = registers[instruction[0] & 15]
            writes.append(address)
            pc += 5
            continue
        if instruction[:4] == bytes.fromhex('7a006d0a'):
            registers[0] = 0x6d << 16
            pc += 4
            continue
        raise AssertionError((hex(pc), instruction.hex()))
    else:
        raise AssertionError('Hook failed to return to original handler')
    assert writes == [0x6d9a07, 0x6d9a08, 0x6d9a3b, 0x6d9a3c]
    assert registers[0] == 0x6d << 16  # displaced instruction restored
    assert all(registers[i] == original_registers[i] for i in range(16) if i not in (0, 9, 10))
    wire = bytes(memory[BASE + i] for i in range(174))
    expected_rate = 44100 if selection == 0 else 48000
    for old, new in zip(descriptors(initial), descriptors(wire)):
        if len(new) == 11 and new[1:4] == bytes.fromhex('240201'):
            assert new[:8] == old[:8]
            assert int.from_bytes(new[8:], 'little') == expected_rate
        else:
            assert old == new
    # Configuration request handler sends min(wLength,wTotalLength), including
    # the common initial nine-byte query and subsequent complete query.
    for requested in [0, 1, 8, 9, 173, 174, 180, 255, 65535]:
        response = wire[:min(requested, int.from_bytes(wire[2:4], 'little'))]
        assert len(response) == min(requested, 174)
        assert response == wire[:len(response)]
    cases.append(dict(selection=selection, rate=expected_rate, steps=steps, writes=writes))

for address, count in manifest['bypasses']:
    raw = read(address, 4)
    assert raw[0] == 0x6a and int.from_bytes(raw[1:], 'big') == address + count
assert read(0x6d902c * 2, 10).decode('utf-16-be') == 'RATE\0'
print('PASS: 48 actual-hook cases; 432 modeled request lengths; exact rate writes and return state. Not full DSP/peripheral emulation.')
