#!/usr/bin/env python3
"""Maintainer tool: produce a deterministic sparse XOR patch from local images."""
import argparse
import json
from pathlib import Path
from patch_firmware import sha, parse, apply, write_new

def make_target(base, image):
    if len(base) != len(image) or parse(base) != parse(image):
        raise ValueError('Images must have the same size and section layout')
    runs = []
    i = 0
    while i < len(base):
        if base[i] == image[i]:
            i += 1
            continue
        start = i
        while i < len(base) and base[i] != image[i]:
            i += 1
        runs.append({'offset': start, 'xor': bytes(a ^ b for a, b in zip(base[start:i], image[start:i])).hex()})
    return {'sha256': sha(image), 'runs': runs}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original', required=True, type=Path)
    p.add_argument('--system', required=True, type=Path)
    p.add_argument('--sd', required=True, type=Path)
    p.add_argument('--output', required=True, type=Path)
    p.add_argument('--revision', default='dynamic-usb-rate')
    args = p.parse_args()
    base = args.original.read_bytes()
    patch = {'format': 'h4n-xor-v1', 'release': '1.9C', 'revision': args.revision, 'base': {'size': len(base), 'sha256': sha(base)}, 'targets': {}}
    for variant, path in [('system', args.system), ('sd', args.sd)]:
        image = path.read_bytes()
        patch['targets'][variant] = make_target(base, image)
        if apply(base, patch, variant) != image:
            raise ValueError('Round-trip verification failed')
    write_new(args.output, (json.dumps(patch, indent=2) + '\n').encode())

if __name__ == '__main__':
    main()
