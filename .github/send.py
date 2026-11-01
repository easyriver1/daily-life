#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日一条：选出今天的文章，推到手机。

通道按环境变量自动选择（谁有值用谁，Server酱优先）：
  SERVERCHAN_SENDKEY  → Server酱 Turbo，推到微信服务号，免费每天 5 条
  PUSHPLUS_TOKEN      → pushplus，需完成实名认证

可选环境变量：
  START_DATE   起始日期，默认 2026-11-02（daily.yml 里的值为准）
  FORCE_INDEX  强制发第 N 篇，用于重发给手机验证排版
  DRY_RUN      只打印将要发送的内容，不真发
"""
import datetime
import glob
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DEFAULT_START = "2026-11-01"


def today_beijing():
    """GitHub runner 用 UTC，+8 小时换成北京时间。"""
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=8)).date()


def pick_file():
    """按文件名排序 + 起始日推算今天该发第几篇。"""
    files = sorted(glob.glob("articles/*.md"))
    if not files:
        sys.exit("articles/ 目录下没有 .md 文件")

    start = datetime.date.fromisoformat(os.environ.get("START_DATE", DEFAULT_START))
    index = (today_beijing() - start).days + 1

    if os.environ.get("FORCE_INDEX"):
        index = int(os.environ["FORCE_INDEX"])

    index = max(1, min(index, len(files)))
    return files[index - 1], index, len(files)


def parse_article(path):
    """拆成 标题 / 正文 / 出处行。格式见 articles/001-野生蘑菇.md。"""
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")

    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:]).strip()

    # 末尾 <sub>…</sub> 是出处角标
    source = ""
    m = re.search(r"<sub>(.*?)</sub>", body, re.S)
    if m:
        source = m.group(1).strip()
        body = body[: m.start()]

    # 去掉正文与出处之间的 --- 分隔线
    body = re.sub(r"(?m)^\s*-{3,}\s*$", "", body).strip()
    return title, body, source


def to_markdown(body, source):
    """Server酱 的 desp 只吃 Markdown，不吃 HTML。"""
    text = body
    if source:
        text += "\n\n" + "*" + source + "*"
    return text


def to_html(body, source):
    """pushplus 的 html 模板认 <br> 与内联样式。"""
    text = body.replace("\n", "<br>")
    if source:
        text += ('<br><br><span style="color:#888888;font-size:12px">'
                 + source + "</span>")
    return text


def send_serverchan(key, title, desp):
    url = "https://sctapi.ftqq.com/%s.send" % urllib.parse.quote(key, safe="")
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode("utf-8")
    try:
        code = json.loads(raw).get("code")
    except ValueError:
        code = None
    if code != 0:
        sys.exit("Server酱 推送失败：%s" % raw)
    return raw


def send_pushplus(token, title, html):
    payload = {"token": token, "title": title, "content": html, "template": "html"}
    req = urllib.request.Request(
        "https://www.pushplus.plus/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    path, index, total = pick_file()
    title, body, source = parse_article(path)

    sc_key = os.environ.get("SERVERCHAN_SENDKEY")
    pp_token = os.environ.get("PUSHPLUS_TOKEN")
    dry = bool(os.environ.get("DRY_RUN"))

    if not dry and not sc_key and not pp_token:
        sys.exit("缺少 SERVERCHAN_SENDKEY 或 PUSHPLUS_TOKEN 环境变量 / GitHub Secret")

    if dry:
        print("第 %d/%d 篇：%s" % (index, total, path))
        print("标题：%s" % title)
        print("正文：%d 字" % len(body))
        print("出处：%s" % (source or "（无）"))
        print("通道：%s" % ("Server酱" if sc_key else ("pushplus" if pp_token else "未配置")))
        print("-" * 40)
        print(to_markdown(body, source))
        return

    if sc_key:
        print("第 %d/%d 篇：%s" % (index, total, path))
        print(send_serverchan(sc_key, title, to_markdown(body, source)))
    else:
        print("第 %d/%d 篇：%s" % (index, total, path))
        print(send_pushplus(pp_token, title, to_html(body, source)))


if __name__ == "__main__":
    main()
