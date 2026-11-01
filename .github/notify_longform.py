#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推一条「新长文上线」的短提醒。长文正文不上微信，只发通知。

环境变量：
  SERVERCHAN_SENDKEY / PUSHPLUS_TOKEN  至少一个
  LF_TITLE   长文标题
  LF_URL     长文链接（通常是 https://easyriver1.github.io/daily-life/#longform）
  LF_SUMMARY 可选，一句话简介
"""
import json
import os
import sys
import urllib.parse
import urllib.request


def send_serverchan(key, title, desp):
    url = "https://sctapi.ftqq.com/%s.send" % urllib.parse.quote(key, safe="")
    data = urllib.parse.urlencode({"title": title, "desp": desp}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded; charset=utf-8"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def send_pushplus(token, title, content):
    payload = {"token": token, "title": title, "content": content, "template": "html"}
    req = urllib.request.Request(
        "https://www.pushplus.plus/send",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8")


def main():
    title = os.environ.get("LF_TITLE") or "新长文"
    url = os.environ.get("LF_URL") or "https://easyriver1.github.io/daily-life/"
    summary = os.environ.get("LF_SUMMARY") or ""

    text = "**%s**\n\n%s\n\n到网页版「长文」栏目读：[点这里打开](%s)" % (
        title, summary, url
    )
    html = "%s<br><br>%s<br><br><a href=\"%s\">到网页版「长文」栏目读</a>" % (
        title, summary, url
    )

    key = os.environ.get("SERVERCHAN_SENDKEY")
    token = os.environ.get("PUSHPLUS_TOKEN")
    if key:
        print(send_serverchan(key, "新长文已上线", text))
    elif token:
        print(send_pushplus(token, "新长文已上线", html))
    else:
        sys.exit("缺少推送凭据")


if __name__ == "__main__":
    main()
