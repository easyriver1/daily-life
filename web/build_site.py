#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""把 articles/*.md 编译成一个静态 PWA 站点。

产物：docs/index.html（全部文章内嵌为 JSON，前端按日期挑当天那篇）
这样「今天该看哪篇」由浏览器算，服务端不需要每天重新构建。
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

START_DATE = "2026-11-02"


def parse_article(path):
    text = io.open(path, encoding="utf-8").read().strip()
    lines = text.split("\n")
    title = lines[0].lstrip("# ").strip()
    rest = "\n".join(lines[1:]).strip()

    source = ""
    # 出处行形如 <sub>...</sub>，前面通常有一行 ---
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


DEMO_TITLES = [
    "每天一小把坚果，28 克就够",
    "维生素 C 防不了感冒，你可能白吃了好几年",
    "「借卡走个账给你几百块」——这是帮信罪",
    "每晚睡 7 小时，作息固定",
    "别指望通用体检套餐能防病",
    "普通感冒别找医生要抗生素",
    "不用信用卡最低还款，不为消费开分期",
    "不借银行卡、手机卡、支付账号",
    "起冲突先报警不动手",
    "喝含糖饮料，换成无糖的也不算解决",
    "体检出了胆囊结石但没疼过，别急着切",
    "每年做一次个税汇算",
    "骑电动车头盔要扣好扣带",
    "十八岁那年 10 月 31 日前要做兵役登记",
    "别为了防癌吃抗氧化补剂",
    "别买甩棍、电击器防身",
]


def demo_articles(real_count):
    """只用于预览排版，不写进仓库。"""
    out = []
    for i, t in enumerate(DEMO_TITLES):
        out.append({
            "title": t,
            "html": "<p><em>（占位内容，仅用于预览排版）</em></p>"
                    "<p>这一篇还没有写。等正文完成后，这里会是一段 300–500 字的短文，"
                    "开头是一个生活场景，中间是可回溯的数字，结尾一句能落地的话。</p>",
            "source": "第 X 节第 Y 条 · 证据 A · 占位",
            "file": "demo-%02d.md" % (i + 2),
        })
    return out[: max(0, 4 - real_count)]


def main():
    files = sorted(glob.glob(os.path.join(ARTICLES, "*.md")))
    if not files:
        raise SystemExit("articles/ 下没有 .md 文件")

    arts = [parse_article(f) for f in files]

    if "--demo" in os.sys.argv:
        arts += demo_articles(len(arts))

    os.makedirs(SITE, exist_ok=True)
    for name in ("manifest.json", "icon.svg", "sw.js"):
        src = os.path.join(ROOT, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(SITE, name))

    tpl = io.open(os.path.join(ROOT, "template.html"), encoding="utf-8").read()
    out = (
        tpl.replace("__ARTICLES__", json.dumps(arts, ensure_ascii=False))
        .replace("__START_DATE__", START_DATE)
        .replace("__COUNT__", str(len(arts)))
    )
    io.open(os.path.join(SITE, "index.html"), "w", encoding="utf-8").write(out)
    print("文章 %d 篇 -> %s" % (len(arts), os.path.join(SITE, "index.html")))


if __name__ == "__main__":
    main()
