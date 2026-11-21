#!/usr/bin/env python3
"""Extract every visible sentence from textbook.js templates, including nested
template literals inside ${... ? `...` : ``} conditionals that jslex treats as
one opaque outer string. This closes the gap left by extract_textbook_long.py.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools' / 'textbook_all.json'

src = (ROOT / 'textbook.js').read_text(encoding='utf-8')


def split_templates(source):
    """Return all backtick-delimited template bodies, including nested ones.

    Uses an explicit stack of contexts ('template' / 'expr') so that nested
    templates inside ${cond ? `...` : ``} are captured as independent bodies.
    A backtick closes a template only when the top context is 'template'.
    """
    bodies = []
    stack = []  # 'template' or 'expr'
    starts = []  # start offsets aligned with template pushes
    i = 0
    n = len(source)
    while i < n:
        if source[i] == '\\':
            i += 2
            continue
        if source.startswith('${', i):
            stack.append('expr')
            i += 2
            continue
        if source[i] == '`':
            if stack and stack[-1] == 'template':
                start = starts.pop()
                stack.pop()
                bodies.append(source[start:i])
            else:
                stack.append('template')
                starts.append(i + 1)
            i += 1
            continue
        if source[i] == '}' and stack and stack[-1] == 'expr':
            stack.pop()
            i += 1
            continue
        i += 1
    return bodies


def strip_interpolations(s):
    """Remove ${...} expressions with balanced-brace matching (handles nesting)."""
    out = []
    i = 0
    n = len(s)
    while i < n:
        if s[i] == '$' and i + 1 < n and s[i + 1] == '{':
            depth = 0
            i += 2
            while i < n and depth >= 0:
                if s[i] == '{':
                    depth += 1
                elif s[i] == '}':
                    depth -= 1
                i += 1
            out.append(' ')
        else:
            out.append(s[i])
            i += 1
    return ''.join(out)


def sentences(body):
    out = []
    # Nested template bodies are captured separately by split_templates(); here
    # we strip every ${...} (balanced) so only literal visible text remains.
    cleaned = strip_interpolations(body)
    for part in re.split(r'</?[A-Za-z][^>]*>', cleaned):
        for line in part.split('\n'):
            s = re.sub(r'\s+', ' ', line).strip()
            if len(s) < 10 or not re.search(r'[A-Za-z]{3}', s):
                continue
            if re.fullmatch(r'[\d\s\W]+', s):
                continue
            out.append(s)
    return out


bodies = split_templates(src)
items = []
seen = set()
for b in bodies:
    for s in sentences(b):
        if s not in seen:
            seen.add(s)
            items.append(s)

OUT.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
print('templates', len(bodies), 'sentences', len(items), 'chars', sum(len(x) for x in items))
for s in items[:20]:
    print(repr(s[:130]))
