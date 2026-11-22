"""极简 JS 词法扫描器：定位字符串字面量（含模板字符串）与注释，供汉化提取/回填使用。

设计目标：只做「字符串定位」这一件事，不解析 AST。所有替换均按
(起始偏移, 结束偏移, 内容) 三元组进行，回填时从后往前替换，保证偏移不失效。
"""
import re

# 字符串起始判定：允许前面出现的合法前缀字符
# 若 ' 或 " 前面是标识符字符或 ) ] 等，则它更可能是除法/撇号，但 JS 中撇号只出现在
# 字符串/注释中，因此对 ' 和 " 直接按字符串处理是安全的。
# `/` 需要区分除法与正则，单独处理。


def scan(src):
    """返回 (strings, comments)。

    strings: list of dict(open, close, quote, raw, start, end)
        start/end 为字面量在源码中的绝对偏移（含引号）。
        raw 为引号内的原始文本（保留转义序列原样）。
    comments: list of (start, end) 注释区间。
    """
    n = len(src)
    i = 0
    strings = []
    comments = []

    # 记录每个位置之前的最后一个「有效字符」，用于判断 / 是除法还是正则
    def prev_significant(pos):
        j = pos - 1
        while j >= 0 and src[j] in ' \t\r\n':
            j -= 1
        return src[j] if j >= 0 else ''

    while i < n:
        c = src[i]

        # 行注释
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            j = src.find('\n', i)
            if j == -1:
                j = n
            comments.append((i, j))
            i = j
            continue

        # 块注释
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            j = src.find('*/', i + 2)
            j = n if j == -1 else j + 2
            comments.append((i, j))
            i = j
            continue

        # 正则字面量：仅当 / 出现在「期望表达式」的位置时
        if c == '/':
            p = prev_significant(i)
            if p == '' or p in '(,=:[!&|?{};+-*%~^<>' or src[max(0, i - 2):i] in ('=>',):
                # 跳过正则体
                j = i + 1
                in_class = False
                while j < n:
                    if src[j] == '\\':
                        j += 2
                        continue
                    if src[j] == '[':
                        in_class = True
                    elif src[j] == ']':
                        in_class = False
                    elif src[j] == '/' and not in_class:
                        break
                    elif src[j] == '\n':
                        break
                    j += 1
                # 跳过 flags
                j += 1
                while j < n and src[j].isalpha():
                    j += 1
                i = j
                continue
            i += 1
            continue

        # 字符串字面量
        if c in ('"', "'"):
            q = c
            j = i + 1
            while j < n:
                if src[j] == '\\':
                    j += 2
                    continue
                if src[j] == q:
                    break
                if src[j] == '\n':
                    # 未闭合（异常），保守终止
                    break
                j += 1
            strings.append(dict(quote=q, start=i, end=j + 1, raw=src[i + 1:j]))
            i = j + 1
            continue

        # 模板字符串
        if c == '`':
            j = i + 1
            while j < n:
                if src[j] == '\\':
                    j += 2
                    continue
                if src[j] == '`':
                    break
                j += 1
            strings.append(dict(quote='`', start=i, end=j + 1, raw=src[i + 1:j]))
            i = j + 1
            continue

        i += 1

    return strings, comments


def in_comment(pos, comments):
    for a, b in comments:
        if a <= pos < b:
            return True
    return False


def decode_js_string(raw, quote):
    """把 JS 字面量内部文本解码为实际字符串（处理常见转义）。"""
    out = []
    i = 0
    n = len(raw)
    while i < n:
        c = raw[i]
        if c == '\\' and i + 1 < n:
            e = raw[i + 1]
            # 行延续符：反斜杠 + 真实换行 → 什么也不输出。
            # 若不特判，'\\' + '\n' 会被映射表当成 '\n' 转义，凭空多出一个换行。
            if e == '\n':
                i += 2
                continue
            if e == '\r':
                i += 3 if raw[i + 2:i + 3] == '\n' else 2
                continue
            mapping = {'n': '\n', 't': '\t', 'r': '\r', 'b': '\b', 'f': '\f',
                       'v': '\v', '0': '\0', "'": "'", '"': '"', '`': '`',
                       '\\': '\\', '/': '/'}
            if e in mapping:
                out.append(mapping[e])
                i += 2
                continue
            if e == 'u':
                if i + 2 < n and raw[i + 2] == '{':
                    k = raw.find('}', i + 3)
                    if k != -1:
                        try:
                            out.append(chr(int(raw[i + 3:k], 16)))
                        except ValueError:
                            out.append(raw[i:k + 1])
                        i = k + 1
                        continue
                try:
                    out.append(chr(int(raw[i + 2:i + 6], 16)))
                    i += 6
                    continue
                except ValueError:
                    pass
            if e == 'x':
                try:
                    out.append(chr(int(raw[i + 2:i + 4], 16)))
                    i += 4
                    continue
                except ValueError:
                    pass
            out.append(e)
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def encode_js_string(text, quote):
    """把实际文本编码回 JS 字面量内部文本。"""
    out = text.replace('\\', '\\\\')
    out = out.replace('\n', '\\n').replace('\r', '\\r')
    if quote == "'":
        out = out.replace("'", "\\'")
    elif quote == '"':
        out = out.replace('"', '\\"')
    elif quote == '`':
        out = out.replace('`', '\\`')
    return out


if __name__ == '__main__':
    import sys
    src = open(sys.argv[1], encoding='utf-8').read()
    ss, cs = scan(src)
    print(f'strings={len(ss)} comments={len(cs)}')
    for s in ss[:20]:
        print(repr(decode_js_string(s['raw'], s['quote']))[:100])
