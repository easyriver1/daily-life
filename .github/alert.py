#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""推送失败时，用还能用的通道发一条告警，避免静默失败。

由 workflow 的 `if: failure()` 步骤调用，环境变量：
  SERVERCHAN_SENDKEY / PUSHPLUS_TOKEN  至少一个
  ALERT_TEXT  可选，默认说明这是自动告警
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
    title = "【告警】今日推送失败"
    text = os.environ.get("ALERT_TEXT") or (
        "每日推送的自动化任务失败了。\n\n"
        "去仓库的 Actions 页面看红色那一步的日志。\n"
        "在它修好之前，你会收不到每日内容。"
    )

    key = os.environ.get("SERVERCHAN_SENDKEY")
    token = os.environ.get("PUSHPLUS_TOKEN")

    if key:
        print(send_serverchan(key, title, text))
    elif token:
        print(send_pushplus(token, title, text.replace("\n", "<br>")))
    else:
        print("没有任何推送凭据，告警无法发出")
        sys.exit(0)


if __name__ == "__main__":
    main()
