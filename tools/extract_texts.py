#!/usr/bin/env python3
"""Extract display-text candidates from Algebraic-Progression source.

Outputs tools/extracted.json. Only produces candidates; translation is a
separate step so that build can be re-run after upstream updates.
"""
import json
import os
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jslex

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent / "extracted.json"

SKIP_DIRS = {"vendor", "tools", ".git", "backup", "screenshots"}
SKIP_FILES = {"break_eternity.js", "panzoom.js", "notify.js", "jquery-3.6.1.js", "vue-2.6.12.js", "vue-2.6.12.min.js"}
DISPLAY_PROPS = (
    "title|desc|description|chargedDesc|name|text|message|tooltip|effect|"
    "requirement|goal|label|note|hint|content|benefit|reward|text1|text2|"
    "unlockText|descriptionText|display|flavor|quote|warning"
)
PROP_RE = re.compile(r"(?:" + DISPLAY_PROPS + r")\s*:\s*$")
CALL_RE = re.compile(r"(?:notify|alert|confirm|prompt|log|print)\s*\(\s*$")
CODE_HINT_RE = re.compile(
    r"^(?:https?:|www\.|#|\.|/|\\)|"
    r"\.(?:js|css|png|jpg|html|json|md)(?:\b|$)|"
    r"^(?:APSave|APSaveMetaData|idk)$|"
    r"^[a-zA-Z][\w-]*\([^)]*\)$"
)


class HTMLTextParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.items = []
        self.skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip_depth += 1
        if self.skip_depth:
            return
        for k, v in attrs:
            if k in ("title", "placeholder", "alt", "aria-label", "data-text", "content") and v:
                self.items.append((v.strip(), "attr:" + k))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.skip_depth:
            self.skip_depth -= 1

    def handle_data(self, data):
        if self.skip_depth or not data or not data.strip():
            return
        # Split around Vue interpolations so each literal fragment is separate.
        for part in re.split(r"(\{\{.*?\}\})", data, flags=re.S):
            if not part or part.startswith("{{"):
                continue
            if re.search(r"[A-Za-z]{2}", part):
                self.items.append((part, "html-text"))


def is_likely_display(raw: str, context: str) -> bool:
    if len(raw) < 2 or len(raw) > 2000:
        return False
    if re.fullmatch(r"[\s\d\W]+", raw):
        return False
    if CODE_HINT_RE.search(raw):
        return False
    if raw.count("\n") > 8:
        return False
    # At least two natural-language characters.
    return bool(re.search(r"[A-Za-z\u4e00-\u9fff]", raw))


def main():
    candidates = {}

    def add(en, kind, source, context):
        if not is_likely_display(en, context):
            return
        key = en
        if key not in candidates:
            candidates[key] = {"en": en, "kind": kind, "contexts": [], "sources": []}
        rec = candidates[key]
        if context not in rec["contexts"]:
            rec["contexts"].append(context)
        if source not in rec["sources"]:
            rec["sources"].append(source)

    # ---- HTML ----
    for name in ("index.html", "changelog.html"):
        path = ROOT / name
        if not path.exists():
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        parser = HTMLTextParser()
        parser.feed(src)
        for text, context in parser.items:
            add(text, "exact", name, context)
            stripped = text.strip()
            if stripped != text:
                add(stripped, "exact", name, context + ":trim")

    # ---- JS ----
    for path in sorted(ROOT.rglob("*.js")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts) or path.name in SKIP_FILES:
            continue
        src = path.read_text(encoding="utf-8", errors="replace")
        strings, comments = jslex.scan(src)
        comment_ranges = [c for c in comments if isinstance(c, (tuple, list)) and len(c) >= 2]

        for s in strings:
            start, end = s["start"], s["end"]
            if any(cs <= start < ce for cs, ce in comment_ranges):
                continue
            raw = s["raw"]
            if not raw or len(raw) > 2000:
                continue
            quote = s["quote"]
            if quote == "`":
                # Template literal: turn ${...} into {{0}}, {{1}} placeholders.
                parts = re.split(r"(\$\{[^}]*\})", raw, flags=re.S)
                out, idx = [], 0
                for part in parts:
                    if part.startswith("${"):
                        out.append("{{%d}}" % idx)
                        idx += 1
                    else:
                        out.append(part.replace("\\n", "\n"))
                en = "".join(out)
                if idx:
                    add(en, "template", str(rel), "js-template")
                    continue
            else:
                try:
                    en = json.loads('"' + raw.replace('\n', '\\n') + '"')
                except Exception:
                    en = raw.replace("\\n", "\n").replace("\\'", "'").replace('\\"', '"')

            line_start = src.rfind("\n", 0, start) + 1
            prefix = src[line_start:start]
            suffix = src[end:end + 80]
            context = "js-other"
            if PROP_RE.search(prefix):
                context = "js-display-prop"
            elif CALL_RE.search(prefix):
                context = "js-call"
            elif re.search(r"^\s*:\s*$", suffix):
                # Object key or ternary label; still often display text, keep but mark.
                context = "js-possible-key"
            add(en, "exact", str(rel), context)

    data = {
        "upstream": "https://github.com/LinLei0102/Algebraic-Progression",
        "commit": "5502337ad6197388ba7617d78f61083846c62e1d",
        "count": len(candidates),
        "candidates": sorted(candidates.values(), key=lambda x: x["en"]),
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    print("candidates:", len(candidates))
    from collections import Counter
    print("contexts:", Counter(c for v in candidates.values() for c in v["contexts"]).most_common(12))
    print("sources:", len({s for v in candidates.values() for s in v["sources"]}))


if __name__ == "__main__":
    main()
