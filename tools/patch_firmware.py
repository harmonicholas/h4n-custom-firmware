#!/usr/bin/env python3
"""Reconstruct an exact release from a user-supplied official firmware image."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]

def sha(data):
    return hashlib.sha256(data).hexdigest()

def parse(data):
    """Return (code byte address, byte size, file offset) for each load section."""
    if len(data) < 0x108:
        raise ValueError('Truncated firmware header')
    p = 0x108 + 4 * struct.unpack_from('>I', data, 0x104)[0]
    sections = []
    while p + 4 <= len(data):
        n = struct.unpack_from('>I', data, p)[0]
        if n == 0:
            return sections, p
        if p + 8 > len(data):
            break
        a = struct.unpack_from('>I', data, p + 4)[0]
        offset = p + 8 + (a & 1)
        if offset + n > len(data):
            break
        sections.append((a, n, offset))
        p = (offset + n + 1) & ~1
    raise ValueError('Invalid firmware section table')

def file_offset(sections, address):
    for a, n, offset in sections:
        if a <= address < a + n:
            return offset + address - a
    raise ValueError(f'Unmapped address: {address:#x}')

def apply(base, patch, variant):
    if patch.get('format') != 'h4n-xor-v1':
        raise ValueError('Unsupported patch format')
    if len(base) != patch['base']['size'] or sha(base) != patch['base']['sha256']:
        raise ValueError('Wrong original firmware. This patch requires the exact official H4n 1.90 image; see README.')
    target = patch['targets'][variant]
    out = bytearray(base)
    end = 0
    for run in target['runs']:
        offset = run['offset']
        delta = bytes.fromhex(run['xor'])
        if type(offset) is not int or not delta or offset < end or offset + len(delta) > len(base):
            raise ValueError('Overlapping or out-of-bounds patch run')
        for i, value in enumerate(delta):
            out[offset + i] ^= value
        end = offset + len(delta)
    if sha(out) != target['sha256']:
        raise ValueError('Output hash mismatch; no file written')
    if int.from_bytes(out[252:256], 'big') != sum(out[256:]) & 0xffffffff:
        raise ValueError('Firmware checksum mismatch')
    if parse(base) != parse(out):
        raise ValueError('Unexpected section layout change')
    return bytes(out)

def write_new(path, data):
    # Exclusive creation: never overwrite source, previous build, or SD files.
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(data)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('original', type=Path, help='Official H4n 1.90 SYSTEM.BIN')
    p.add_argument('--variant', choices=('system', 'sd'), default='sd')
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    try:
        patch = json.loads((ROOT / 'patches/1.9C.json').read_text())
        result = apply(args.original.read_bytes(), patch, args.variant)
        write_new(args.output, result)
    except (OSError, ValueError, KeyError, TypeError) as error:
        p.exit(1, f'Error: {error}\n')
    print(f'Created {args.output} ({len(result)} bytes)\nSHA256 {sha(result)}')
    print('No device or SD card was modified automatically.')

if __name__ == '__main__':
    main()
