#!/usr/bin/env python3
"""Merge translated chunks into the runtime dictionary and validate them."""
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARTS = sorted((ROOT / "tools" / "translations").glob("part_*.json"))
OUT = ROOT / "i18n" / "dict.js"
CONFLICTS = ROOT / "docs" / "译法冲突.md"

PH_RE = re.compile(r"\{\{\d+\}\}|%[sd]|\{\d+\}")
TAG_RE = re.compile(r"</?[A-Za-z][^>]*>")
MARK_RE = re.compile(r"\[(?:red|rainbow|green|blue|yellow|gray)\]")


def multiset(regex, s):
    return Counter(regex.findall(s))


def main():
    merged = {}
    sources = defaultdict(list)
    conflicts = []
    invalid = []

    patch_path = ROOT / "tools" / "patch_zh.json"
    vue_patch_path = ROOT / "tools" / "vue_patch_zh.json"
    sources_list = list(PARTS)
    sources_list += sorted((ROOT / "tools" / "textbook_translations").glob("tb_*.json"))
    if patch_path.exists():
        sources_list.append(patch_path)
    if vue_patch_path.exists():
        sources_list.append(vue_patch_path)

    for p in sources_list:
        try:
            rows = json.loads(p.read_text(encoding="utf-8-sig"))
        except Exception as e:
            print("SKIP invalid JSON", p.name, e)
            continue
        if isinstance(rows, dict):
            rows = [{"en": k, "zh": v} for k, v in rows.items()]
        for row in rows:
            if not isinstance(row, dict):
                continue
            en, zh = row.get("en"), row.get("zh")
            if not isinstance(en, str) or not isinstance(zh, str) or not en.strip() or not zh.strip():
                continue
            if en in merged and merged[en] != zh:
                conflicts.append((en, merged[en], zh, p.name))
                sources[en].append(p.name)
                continue
            merged[en] = zh
            sources[en].append(p.name)

    harmony = {
        "Y二次": "Y-二次", "Y 二次": "Y-二次", "Y-Quadratic": "Y-二次",
        "迷失积分": "遗失积分", "根本质": "根精华", "发生器": "生成器",
        "量子力": "量子", "三角波": "三角波",
    }
    exact, patterns = {}, []
    for en, zh in sorted(merged.items()):
        for a, b in harmony.items():
            zh = zh.replace(a, b)
        if zh == en:
            continue
        problems = []
        for label, rx in (("placeholder", PH_RE), ("tag", TAG_RE), ("mark", MARK_RE)):
            a, b = multiset(rx, en), multiset(rx, zh)
            if a != b:
                problems.append(f"{label}: {dict(a)} != {dict(b)}")
        if problems:
            invalid.append((en, zh, "; ".join(problems)))
            continue
        if PH_RE.search(en):
            patterns.append({"en": en, "zh": zh})
        else:
            exact[en] = zh

    def is_phrase_key(en):
        if len(en) < 3 or re.search(r"[<>\n]", en):
            return False
        if " " in en or en[:1].isupper():
            return True
        # 纯小写短词（seconds/second/completed 等）在 Vue 插值拼接节点里高频出现，
        # 需纳入短语表才能在「半英半中」节点中命中。
        return bool(re.fullmatch(r"[a-z]+", en))

    phrases = [
        {"en": en, "zh": zh}
        for en, zh in sorted(exact.items())
        if is_phrase_key(en)
    ]

    payload = {"exact": exact, "patterns": patterns, "phrases": phrases}
    OUT.write_text(
        "window.AP_ZH_DATA = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )

    lines = [
        "# 译法冲突与校验报告",
        "",
        f"- 合并分片：{len(PARTS)}",
        f"- 译文条目：{len(merged)}",
        f"- 整串词条：{len(exact)}",
        f"- 模板词条：{len(patterns)}",
        f"- 短语表条目：{len(phrases)}",
        f"- 冲突条目：{len(conflicts)}",
        f"- 占位符/标签校验失败：{len(invalid)}",
        "",
        "## 冲突（按术语表人工裁决，取首个译法）",
        "",
    ]
    for en, a, b, src in conflicts[:200]:
        lines.append(f"- `{en}`\n  - {a}（{', '.join(sources.get(en, []))}）\n  - {b}（{src}）")
    if not conflicts:
        lines.append("- 无")
    lines += ["", "## 校验失败（未进入词典）", ""]
    for en, zh, why in invalid[:200]:
        lines.append(f"- `{en}` → `{zh}`：{why}")
    if not invalid:
        lines.append("- 无")
    CONFLICTS.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"parts={len(PARTS)} merged={len(merged)} exact={len(exact)} patterns={len(patterns)} phrases={len(phrases)} conflicts={len(conflicts)} invalid={len(invalid)}")
    print("dict.js bytes:", OUT.stat().st_size)


if __name__ == "__main__":
    main()
