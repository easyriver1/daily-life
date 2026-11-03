#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 articles/<栏目>/*.md 编译成一个多栏目的静态 PWA 站点。

规则：
  - 栏目定义、名称、排期全部来自 articles/_manifest.json（唯一状态源）
  - 没有内容的栏目自动隐藏，不会出现空标签
  - 文章里带 <!-- noindex --> 标记的（有版权的内容）不上站点，只在微信推送
产物：docs/index.html —— 全部文章内嵌为 JSON，前端按排期挑当天那篇。
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
MANIFEST = os.path.join(ARTICLES, "_manifest.json")

HIDDEN_MARK = "<!-- noindex -->"


def load_manifest():
    with io.open(MANIFEST, encoding="utf-8") as f:
        return json.load(f)


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
    data_in = load_manifest()
    columns = {}
    meta = {}

    for key, conf in data_in["columns"].items():
        files = sorted(glob.glob(os.path.join(ARTICLES, key, "*.md")))
        arts = []
        for f in files:
            raw = io.open(f, encoding="utf-8").read()
            if HIDDEN_MARK in raw:
                print("  跳过（有版权，不上站点）：%s" % os.path.basename(f))
                continue
            arts.append(parse_article(f))
        if not arts:
            continue  # 空栏目直接隐藏
        columns[key] = arts
        meta[key] = {"name": conf["name"], "desc": conf.get("schedule", "")}

    if not columns:
        raise SystemExit("articles/ 下没有任何可发布的 .md 文件")

    data = {
        "start": data_in["start"],
        "schedule": [data_in["schedule"].get(str(i)) for i in range(7)],
        "columns": columns,
        "meta": meta,
    }

    os.makedirs(SITE, exist_ok=True)
    for name in ("manifest.json", "icon.svg", "sw.js"):
        src = os.path.join(ROOT, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(SITE, name))

    tpl = io.open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    out = tpl.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    io.open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(out)

    total = sum(len(v) for v in columns.values())
    print("站点：%d 个栏目 / %d 篇 -> %s" % (len(columns), total, os.path.join(SITE, "index.html")))
    for k, v in columns.items():
        print("  %s：%d 篇" % (meta[k]["name"], len(v)))


if __name__ == "__main__":
    main()
