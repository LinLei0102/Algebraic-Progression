#!/usr/bin/env python3
"""Extract display sentences from long textbook template literals missed by extract_texts.py."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jslex

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools' / 'textbook_long.json'


def main():
    src = (ROOT / 'textbook.js').read_text(encoding='utf-8')
    strings, _ = jslex.scan(src)
    items = []
    seen = set()
    for token in strings:
        raw = token['raw']
        if not raw or raw.count('\n') <= 8 or not re.search(r'[A-Za-z]{3}', raw):
            continue
        refs = []

        def repl(_m):
            refs.append(1)
            return '{{%d}}' % (len(refs) - 1)

        text = re.sub(r'\$\{[^}]*\}', repl, raw)
        # Split at HTML tags; keep only visible text portions.
        for part in re.split(r'</?[A-Za-z][^>]*>', text):
            for line in part.split('\n'):
                s = line.strip()
                s = re.sub(r'\s+', ' ', s)
                if not s or len(s) < 12 or not re.search(r'[A-Za-z]{3}', s):
                    continue
                if re.fullmatch(r'[\d\s\W]+', s):
                    continue
                if s in seen:
                    continue
                seen.add(s)
                items.append(s)
    OUT.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
    print('segments:', len(items))
    print('chars:', sum(len(s) for s in items))


if __name__ == '__main__':
    main()
