#!/usr/bin/env python3
"""Fail if unexpected/private artifacts enter the public source tree."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_SUFFIXES = {'.md', '.py', '.json', '.yml', '.yaml'}
ALLOWED_NAMES = {'LICENSE', '.gitignore', '.gitattributes'}

def main():
    files = {p.relative_to(ROOT) for p in ROOT.rglob('*') if p.is_file() and p.name != '.DS_Store'
             and not any(x in {'.git', 'build', 'private', '__pycache__', '.venv'} for x in p.relative_to(ROOT).parts)}
    # Also inspect tracked files even if an ignore rule would hide them.
    if (ROOT / '.git').exists():
        result = subprocess.run(['git', 'ls-files', '-z'], cwd=ROOT, capture_output=True, check=True)
        files.update(Path(x.decode()) for x in result.stdout.split(b'\0') if x)
    failures = []
    for rel in sorted(files):
        p = ROOT / rel
        if p.is_symlink() or rel.suffix.lower() not in ALLOWED_SUFFIXES and rel.name not in ALLOWED_NAMES:
            failures.append(f'Unexpected file: {rel}')
            continue
        if any(x in {'build', 'private', 'archive', '__pycache__'} for x in rel.parts):
            failures.append(f'Private/generated path tracked: {rel}')
        try:
            text = p.read_text(encoding='utf-8')
        except (UnicodeError, OSError):
            failures.append(f'Unreadable/non-text file: {rel}')
            continue
        # Construct patterns so the audit does not match its own source.
        patterns = ['/' + 'Users/', '/' + 'Volumes/', 'BEGIN ' + 'PRIVATE KEY',
                    'rollout-' + '2026-', 'api_' + 'key=']
        if any(pattern in text for pattern in patterns):
            failures.append(f'Personal path or secret-like marker: {rel}')
    if failures:
        raise SystemExit('\n'.join(failures))
    print(f'PASS: {len(files)} public text files; no disallowed artifacts or personal-path markers.')
    print('This targeted audit is not a comprehensive secret/license scanner.')

if __name__ == '__main__':
    main()
