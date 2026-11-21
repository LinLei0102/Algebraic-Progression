#!/usr/bin/env python3
"""Extract string literals inside Vue {{ }} interpolations from index.html.

The main HTML parser skips {{...}} entirely, so dynamic ternaries like
{{ cond ? "Buildings" : "Generators" }} never enter the dictionary. These
literals are exactly the fragments that leak English into mixed zh/en nodes.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'tools' / 'vue_literals.json'

src = (ROOT / 'index.html').read_text(encoding='utf-8')

# 抓取所有 {{ ... }} 插值体（含换行，非贪婪到最近的 }}）
interps = re.findall(r'\{\{([\s\S]*?)\}\}', src)

seen = {}
for body in interps:
    # 插值内的字符串字面量："..." 或 '...'
    for m in re.finditer(r'"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\'', body):
        s = m.group(1) if m.group(1) is not None else m.group(2)
        if not s:
            continue
        # 只保留含英文字母的展示型字面量
        if not re.search(r'[A-Za-z]{2}', s):
            continue
        # 排除代码标识符/属性/方法名特征
        if re.search(r'[{}()\[\];=]|\b(player|tmp|true|false|null|format)\b', s):
            continue
        # 排除纯 HTML 标签/类名
        if s.startswith('<') or re.fullmatch(r'[a-z\-]+', s) and len(s) < 6:
            continue
        if s not in seen:
            seen[s] = []

items = sorted(seen.keys())
OUT.write_text(json.dumps(items, ensure_ascii=False, indent=1), encoding='utf-8')
print('interpolations', len(interps), 'literals', len(items))
for s in items:
    print(repr(s))
