import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from patch_firmware import apply, parse, sha, write_new
from make_patch import make_target

class PatchTests(unittest.TestCase):
    def setUp(self):
        # A tiny synthetic load table, not Zoom firmware.
        base = bytearray(384)
        struct.pack_into('>I', base, 0x104, 0)
        struct.pack_into('>II', base, 0x108, 8, 0x1000)
        base[0x110:0x118] = b'original'
        base[252:256] = (sum(base[256:]) & 0xffffffff).to_bytes(4, 'big')
        self.base = bytes(base)
        target = bytearray(base)
        target[0x110:0x118] = b'modified'
        target[252:256] = (sum(target[256:]) & 0xffffffff).to_bytes(4, 'big')
        self.target = bytes(target)
        self.patch = {'format': 'h4n-xor-v1', 'base': {'size': len(base), 'sha256': sha(base)}, 'targets': {'sd': make_target(self.base, self.target)}}

    def test_roundtrip(self):
        self.assertEqual(apply(self.base, self.patch, 'sd'), self.target)

    def test_wrong_source(self):
        with self.assertRaisesRegex(ValueError, 'Wrong original'):
            apply(b'x' + self.base[1:], self.patch, 'sd')

    def test_bad_output_digest(self):
        self.patch['targets']['sd']['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            apply(self.base, self.patch, 'sd')

    def test_overlapping_run(self):
        runs = self.patch['targets']['sd']['runs']
        runs.insert(1, copy.deepcopy(runs[0]))
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            apply(self.base, self.patch, 'sd')

    def test_out_of_bounds(self):
        self.patch['targets']['sd']['runs'] = [{'offset': len(self.base), 'xor': '01'}]
        with self.assertRaisesRegex(ValueError, 'out-of-bounds'):
            apply(self.base, self.patch, 'sd')

    def test_bad_checksum(self):
        target = bytearray(self.target);target[252] ^= 1
        self.patch['targets']['sd'] = make_target(self.base, target)
        with self.assertRaisesRegex(ValueError, 'checksum'):
            apply(self.base, self.patch, 'sd')

    def test_truncated_table(self):
        with self.assertRaises(ValueError):
            parse(self.base[:0x112])

    def test_no_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'firmware.bin'
            write_new(p, b'first')
            with self.assertRaises(FileExistsError):
                write_new(p, b'second')
            self.assertEqual(p.read_bytes(), b'first')

    def test_release_patch_shape(self):
        patch = json.loads((Path(__file__).resolve().parents[1] / 'patches/1.9C.json').read_text())
        self.assertEqual(set(patch['targets']), {'system', 'sd'})
        for target in patch['targets'].values():
            end = 0
            for run in target['runs']:
                data = bytes.fromhex(run['xor'])
                self.assertTrue(data and all(data))
                self.assertGreaterEqual(run['offset'], end)
                end = run['offset'] + len(data)
                self.assertLessEqual(end, patch['base']['size'])

if __name__ == '__main__':
    unittest.main()
