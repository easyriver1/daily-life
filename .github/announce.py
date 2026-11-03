#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""长文上线提醒：按 INDEX 取第 N 篇长文，发一条短通知。

INDEX 由 workflow 根据触发的 cron 决定（第 1/2/3 篇）。
"""
import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from send import parse_article  # noqa: E402
import notify_longform  # noqa: E402


def main():
    idx = int(os.environ.get("INDEX", "1"))
    files = sorted(glob.glob("articles/longform/*.md"))
    if not files:
        sys.exit("没有长文可发")
    idx = max(1, min(idx, len(files)))
    title, body, _ = parse_article(files[idx - 1])
    os.environ["LF_TITLE"] = title
    os.environ.setdefault("LF_SUMMARY", "约 %d 字，手机上读 10 分钟左右。" % len(body))
    print("第 %d/%d 篇：%s" % (idx, len(files), title))
    notify_longform.main()


if __name__ == "__main__":
    main()
