#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验 assets/ 下两份教育部索引：结构、计数、URL 协议/主机/commit 钉扎。

用法: python3 scripts/validate_indexes.py
退出码: 0 = 全部通过, 1 = 存在失败项

条数以本脚本 INDEXES 中的 expected 为单一事实源；SKILL.md / README.md /
AGENTS.md 中出现的条数必须与本脚本运行输出一致，不一致即为文档漂移。
上游镜像仓库更新时：git ls-remote 获取新 commit SHA → 替换索引中的
/raw/<旧SHA>/ → 更新本脚本 expected → 运行本校验 → 同步文档条数。
"""
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (相对路径, URL字段, 期望后缀, 期望条数)
INDEXES = [
    ("assets/moe_pdfs_final.json", "pdf_url", ".pdf", 579),
    ("assets/moe_jianjie_final.json", "md_url", ".md", 1349),
]
BASE_FIELDS = ("major_code", "major_name", "education_level")
ALLOWED_HOST = "github.com"
PIN_RE = re.compile(r"/raw/([0-9a-f]{40})/")

errors = []


def err(msg):
    errors.append(msg)


all_pins = set()

for rel, url_key, suffix, expected in INDEXES:
    path = os.path.join(ROOT, rel)
    if not os.path.isfile(path):
        err("%s: 文件不存在" % rel)
        continue
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        err("%s: JSON 解析失败: %s" % (rel, e))
        continue
    if not isinstance(data, list) or not data:
        err("%s: 应为非空 JSON 数组" % rel)
        continue

    if len(data) != expected:
        err("%s: 条数 %d != 期望 %d（更新索引后请同步本脚本 expected 与文档条数）"
            % (rel, len(data), expected))

    want_keys = set(BASE_FIELDS) | {url_key}
    pins, urls, codes = set(), set(), {}
    for i, rec in enumerate(data):
        where = "%s[%d]" % (rel, i)
        if not isinstance(rec, dict):
            err("%s: 非对象" % where)
            continue
        if set(rec) != want_keys:
            err("%s: 字段集合 %s != 期望 %s" % (where, sorted(rec), sorted(want_keys)))
            continue
        empty = [k for k in want_keys if not str(rec[k]).strip()]
        if empty:
            err("%s: 空值字段 %s" % (where, empty))
            continue

        code = rec["major_code"]
        if code in codes:
            err("%s: major_code %s 与 [%d] 重复" % (where, code, codes[code]))
        else:
            codes[code] = i

        url = rec[url_key]
        urls.add(url)
        parts = urllib.parse.urlparse(url)
        if parts.scheme != "https":
            err("%s: 非 https: %s" % (where, parts.scheme))
        if parts.hostname != ALLOWED_HOST:
            err("%s: 主机不在白名单: %s" % (where, parts.hostname))
        if not url.lower().endswith(suffix):
            err("%s: 后缀非 %s: %s" % (where, suffix, url[-40:]))
        m = PIN_RE.search(url)
        if m:
            pins.add(m.group(1))
            all_pins.add(m.group(1))
        else:
            err("%s: URL 未钉扎 40 位 commit SHA（可变分支 raw/main 禁用）: %s"
                % (where, url[:80]))

    ok = not any(e.startswith(rel + "[") or e.startswith(rel + ":") for e in errors)
    tag = "OK " if ok else "FAIL"
    print("[%s] %s: %d 条, 唯一URL %d, 钉扎SHA %s"
          % (tag, rel, len(data), len(urls),
             ",".join(sorted(pins)) or "无"))

if len(all_pins) > 1:
    err("钉扎 SHA 不唯一（应为同一上游快照）: %s" % ",".join(sorted(all_pins)))
elif len(all_pins) == 1:
    print("[OK ] 快照钉扎: %s（单一致 commit）" % next(iter(all_pins)))

if errors:
    print("\n失败 %d 项:" % len(errors))
    for e in errors:
        print("  - " + e)
    sys.exit(1)
print("\n全部通过")
