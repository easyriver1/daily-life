#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 articles/{books,skills,weekly}/*.md 编译成一个多栏目的静态 PWA 站点。

产物：docs/index.html —— 全部文章内嵌为 JSON，前端按排期挑当天那篇。
docs/ 同时是 GitHub Pages 的发布目录。
"""
import glob
import io
import json
import os
import re
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(ROOT)
ARTICLES = os.path.join(REPO, "articles")
SITE = os.path.join(REPO, "docs")

START_DATE = "2026-11-01"

# 栏目定义：key, 显示名, 排期说明
COLUMNS = [
    ("books", "书", "周一 / 周三 / 周五"),
    ("skills", "技能", "周二 / 周四"),
    ("weekly", "周报", "周六"),
]

# 0=周一 … 6=周日；None = 不发
SCHEDULE = ["books", "skills", "books", "skills", "books", "weekly", None]


def parse_article(path):
    text = io.open(path, encoding="utf-8").read().strip()
    lines = text.split("\n")
    title = lines[0].lstrip("# ").strip()
    rest = "\n".join(lines[1:]).strip()

    source = ""
    m = re.search(r"<sub>(.*?)</sub>", rest, re.S)
    if m:
        source = m.group(1).strip()
        rest = rest[: m.start()].rstrip()
    rest = re.sub(r"-{3,}\s*$", "", rest).strip()

    # markdown 粗体 -> html
    rest = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rest)
    paras = [p.strip() for p in rest.split("\n\n") if p.strip()]
    html = "\n".join("<p>%s</p>" % p.replace("\n", "<br>") for p in paras)

    return {
        "title": title,
        "html": html,
        "source": source,
        "file": os.path.basename(path),
    }


def main():
    columns = {}
    total = 0
    for key, name, desc in COLUMNS:
        files = sorted(glob.glob(os.path.join(ARTICLES, key, "*.md")))
        columns[key] = [parse_article(f) for f in files]
        total += len(files)

    if total == 0:
        raise SystemExit("articles/ 下没有任何 .md 文件")

    data = {
        "start": START_DATE,
        "schedule": SCHEDULE,
        "columns": columns,
        "meta": {k: {"name": n, "desc": d} for k, n, d in COLUMNS},
    }

    os.makedirs(SITE, exist_ok=True)
    for name in ("manifest.json", "icon.svg", "sw.js"):
        src = os.path.join(ROOT, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(SITE, name))

    tpl = io.open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    out = (
        tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
        .replace("__START_DATE__", START_DATE)
    )
    io.open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(out)
    print("文章 %d 篇 -> %s" % (total, os.path.join(SITE, "index.html")))
    for key, name, desc in COLUMNS:
        print("  %s：%d 篇" % (name, len(columns[key])))


if __name__ == "__main__":
    main()
