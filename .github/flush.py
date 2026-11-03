#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量清库存：把 flush-list.txt 里的旧稿一次性发完，分两批。

为什么要有这个：Server酱 免费额度是每天 5 条，9 篇一次发会超限。
所以拆成两批：11-04 发前 5 篇，11-05 发剩下 4 篇。两天内清空，
期间 daily.yml 会自动跳过（见 flush-dates.txt）。

环境变量：
  BATCH    1 或 2
  BATCH1_N 第一批篇数（默认 5）
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from send import parse_article, to_markdown, send_serverchan, send_pushplus  # noqa: E402

LIST = os.path.join(HERE, "..", "flush-list.txt")


def main():
    batch = os.environ.get("BATCH", "1")
    n1 = int(os.environ.get("BATCH1_N", "5"))

    paths = [l.strip() for l in open(LIST, encoding="utf-8") if l.strip()]
    if batch == "2":
        todo = paths[n1:]
    else:
        todo = paths[:n1]

    key = os.environ.get("SERVERCHAN_SENDKEY")
    token = os.environ.get("PUSHPLUS_TOKEN")
    if not key and not token:
        sys.exit("缺少推送凭据")

    print("第 %s 批，共 %d 篇" % (batch, len(todo)))
    dry = bool(os.environ.get("DRY_RUN"))
    for p in todo:
        if not os.path.exists(p):
            print("跳过（文件不存在）：%s" % p)
            continue
        title, body, source = parse_article(p)
        if dry:
            print("[DRY] 将发：%s（%d 字）" % (title, len(body)))
            continue
        if key:
            send_serverchan(key, title, to_markdown(body, source))
        else:
            send_pushplus(token, title, to_markdown(body, source))
        print("已发：%s" % title)


if __name__ == "__main__":
    main()
