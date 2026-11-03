#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""每日一条：按星期几选栏目，推送当天那一篇。

排期（周日不发）：
  周一 / 周三 / 周五  -> articles/books   书线
  周二 / 周四         -> articles/skills  技能线
  周六                -> articles/weekly  周报

栏目内按文件名排序，第 N 次推送取第 N 个文件；序号由「从 START_DATE 起该栏目
已经排到第几次」算出，不依赖任何状态文件，漏跑一天也不会错位。

通道（谁有值用谁，Server酱优先）：
  SERVERCHAN_SENDKEY  → Server酱 Turbo，微信服务号，免费每天 5 条
  PUSHPLUS_TOKEN      → pushplus，需实名

可选环境变量：
  START_DATE   起始日期，默认 2026-11-01
  FORCE_COL    强制栏目 books|skills|weekly（测试用）
  FORCE_INDEX  强制发该栏目的第 N 篇（测试用）
  FORCE_DATE   当成某一天来算（YYYY-MM-DD，测试用）
  DRY_RUN      只打印不发送
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

COLUMNS = {
    "books": {"dir": "articles/books", "name": "书"},
    "skills": {"dir": "articles/skills", "name": "常识"},
    "weekly": {"dir": "articles/weekly", "name": "周报"},
    "bits": {"dir": "articles/bits", "name": "小菜"},
}

# 0=周一 ... 6=周日；周日为 None（不发）
SCHEDULE = {0: "books", 1: "skills", 2: "books", 3: "skills", 4: "books", 5: "weekly", 6: None}

# 库存低于这个数就在推送末尾提醒
LOW_STOCK = 3

# 已经发过的篇数（清库存等一次性发送后，从这里记账，避免重发）
PROGRESS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "..", "articles", "_progress.json")


def load_progress():
    try:
        with open(PROGRESS_FILE, encoding="utf-8") as f:
            return json.load(f).get("done", {})
    except (IOError, ValueError):
        return {}


def today_beijing():
    """GitHub runner 用 UTC，+8 小时换成北京时间。"""
    forced = os.environ.get("FORCE_DATE")
    if forced:
        return datetime.date.fromisoformat(forced)
    return (datetime.datetime.now(datetime.timezone.utc)
            + datetime.timedelta(hours=8)).date()


def column_of(day):
    return SCHEDULE.get(day.weekday())


def nth_of_column(start, day, col):
    """从 start 到 day（含）之间，这个栏目排到第几次。"""
    n = 0
    d = start
    while d <= day:
        if column_of(d) == col:
            n += 1
        d += datetime.timedelta(days=1)
    return n


def parse_article(path):
    """拆成 标题 / 正文 / 出处行。"""
    text = open(path, encoding="utf-8").read()
    lines = text.split("\n")

    title = lines[0].lstrip("# ").strip()
    body = "\n".join(lines[1:]).strip()

    source = ""
    m = re.search(r"<sub>(.*?)</sub>", body, re.S)
    if m:
        source = m.group(1).strip()
        body = body[: m.start()]

    body = re.sub(r"(?m)^\s*-{3,}\s*$", "", body).strip()
    return title, body, source


def to_markdown(body, source, note=""):
    text = body
    if source:
        text += "\n\n*" + source + "*"
    if note:
        text += "\n\n---\n\n" + note
    return text


def to_html(body, source, note=""):
    text = body.replace("\n", "<br>")
    if source:
        text += ('<br><br><span style="color:#888888;font-size:12px">'
                 + source + "</span>")
    if note:
        text += ('<br><br><span style="color:#cc8844;font-size:12px">'
                 + note + "</span>")
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


def deliver(title, body, source, note, dry=False):
    sc_key = os.environ.get("SERVERCHAN_SENDKEY")
    pp_token = os.environ.get("PUSHPLUS_TOKEN")

    if dry:
        print("标题：%s" % title)
        print("正文：%d 字" % len(body))
        print("出处：%s" % (source or "（无）"))
        print("通道：%s" % ("Server酱" if sc_key else ("pushplus" if pp_token else "未配置")))
        if note:
            print("附加提示：%s" % note)
        print("-" * 40)
        print(to_markdown(body, source, note))
        return

    if sc_key:
        print(send_serverchan(sc_key, title, to_markdown(body, source, note)))
    elif pp_token:
        print(send_pushplus(pp_token, title, to_html(body, source, note)))
    else:
        sys.exit("缺少 SERVERCHAN_SENDKEY 或 PUSHPLUS_TOKEN 环境变量 / GitHub Secret")


def main():
    start = datetime.date.fromisoformat(os.environ.get("START_DATE", DEFAULT_START))
    today = today_beijing()
    dry = bool(os.environ.get("DRY_RUN"))

    col = os.environ.get("FORCE_COL") or column_of(today)
    if col is None:
        print("今天是周日，不推送。")
        return

    # 两个工作流分工：daily 负责其他六天，weekly 负责周六早上
    mode = os.environ.get("MODE", "")

    # 11:00 那一条是「小菜」：固定走 bits 栏目，与星期几无关
    if mode == "noon":
        col = "bits"
    elif col == "weekly" and mode == "daily":
        print("周六的周报由 weekly.yml 负责，本次跳过。")
        return
    elif mode == "weekly" and col != "weekly":
        print("今天不是周六，周报工作流跳过。")
        return

    # 清库存期间（flush）暂停常规推送，避免超过 Server酱 每天 5 条
    flush_dates = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "flush-dates.txt")
    if os.path.exists(flush_dates):
        dates = [l.strip() for l in open(flush_dates, encoding="utf-8") if l.strip()]
        if today.isoformat() in dates:
            print("今天是批量清库存日，常规推送跳过。")
            return

    files = sorted(glob.glob(os.path.join(COLUMNS[col]["dir"], "*.md")))
    idx = int(os.environ.get("FORCE_INDEX") or (load_progress().get(col, 0) + nth_of_column(start, today, col)))

    print("日期：%s（周%d） 栏目：%s" % (today, today.weekday() + 1, COLUMNS[col]["name"]))

    # 小菜栏目还没写：静默跳过，不发断更提醒
    if not files and col == "bits":
        print("小菜栏目还没有内容，本次跳过。")
        return

    # 该栏目还没有稿件
    if not files:
        deliver("【断更】%s栏目还没有内容" % COLUMNS[col]["name"],
                "今天的「%s」栏目还没有写好的稿子，推送跳过。" % COLUMNS[col]["name"],
                "", "", dry)
        return

    # 稿件用完了：不发旧文，改发一条预警，避免静默重复
    if idx > len(files):
        deliver("【断更】%s栏目稿件已用完" % COLUMNS[col]["name"],
                "今天的「%s」栏目已经没有新稿了（共 %d 篇，已发到第 %d 篇）。\n\n"
                "补稿后会自动恢复。" % (COLUMNS[col]["name"], len(files), len(files)),
                "", "", dry)
        return

    path = files[idx - 1]
    title, body, source = parse_article(path)

    note = ""
    remain = len(files) - idx
    if remain < LOW_STOCK:
        note = "该栏目库存只剩 %d 篇，该补稿了。" % remain

    print("第 %d/%d 篇：%s" % (idx, len(files), path))
    deliver(title, body, source, note, dry)


if __name__ == "__main__":
    main()
