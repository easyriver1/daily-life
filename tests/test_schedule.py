#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""排期逻辑的自动化测试。

为什么要有：`send.py` 的选篇规则靠日期推算 + 清单偏移，改一次就可能
错一天。以前只能手工 DRY_RUN，今天已经踩过「偏移算错导致误报用完」。

跑法（在 site/ 目录下）：
    python -m unittest discover -s tests -v
"""
import datetime
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SITE, ".github"))

import send  # noqa: E402


D = datetime.date.fromisoformat


class TestSchedule(unittest.TestCase):
    """0=周一 … 6=周日"""

    def test_weekday_labels(self):
        self.assertEqual(D("2026-11-02").weekday(), 0)  # 周一
        self.assertEqual(D("2026-11-07").weekday(), 5)  # 周六
        self.assertEqual(D("2026-11-08").weekday(), 6)  # 周日

    def test_column_of(self):
        self.assertEqual(send.column_of(D("2026-11-02")), "books")
        self.assertEqual(send.column_of(D("2026-11-03")), "skills")
        self.assertEqual(send.column_of(D("2026-11-04")), "books")
        self.assertEqual(send.column_of(D("2026-11-05")), "skills")
        self.assertEqual(send.column_of(D("2026-11-06")), "books")
        self.assertEqual(send.column_of(D("2026-11-07")), "weekly")
        self.assertIsNone(send.column_of(D("2026-11-08")), "周日不该有栏目")

    def test_nth_counts_only_own_column(self):
        start = D("2026-11-01")
        # 第一个书日是 11-02，第一个技能日是 11-03
        self.assertEqual(send.nth_of_column(start, D("2026-11-02"), "books"), 1)
        self.assertEqual(send.nth_of_column(start, D("2026-11-03"), "books"), 1)
        self.assertEqual(send.nth_of_column(start, D("2026-11-04"), "books"), 2)
        self.assertEqual(send.nth_of_column(start, D("2026-11-06"), "books"), 3)
        self.assertEqual(send.nth_of_column(start, D("2026-11-05"), "skills"), 2)
        self.assertEqual(send.nth_of_column(start, D("2026-11-07"), "weekly"), 1)
        self.assertEqual(send.nth_of_column(start, D("2026-11-07"), "skills"), 2,
                         "周报日不该让技能计数前进")

    def test_sunday_never_counts(self):
        start = D("2026-11-01")
        for col in send.COLUMNS:
            self.assertEqual(
                send.nth_of_column(D("2026-11-08"), D("2026-11-08"), col), 0,
                "周日不应计入任何栏目")


class TestManifest(unittest.TestCase):
    def test_manifest_has_required_keys(self):
        for key in ("start", "columns", "schedule", "done"):
            self.assertIn(key, send.MANIFEST_DATA, "manifest 缺 %s" % key)

    def test_schedule_points_to_known_columns(self):
        for wd, col in send.SCHEDULE.items():
            if col is None:
                continue
            self.assertIn(col, send.COLUMNS,
                          "排期指向了不存在的栏目：%s" % col)

    def test_done_has_no_unknown_columns(self):
        for col in send.load_progress():
            self.assertIn(col, send.COLUMNS,
                          "done 里出现了不存在的栏目：%s" % col)


class TestIndex(unittest.TestCase):
    """idx = done（清库存已发） + 按排期算出的次数"""

    def test_index_math(self):
        start = send.MANIFEST_DATA["start"]
        done = send.load_progress()
        # 2026-11-05 是第二个技能日，done.skills 应为 0（没用清库存发过技能稿）
        start_d = D(start)
        idx = done.get("skills", 0) + send.nth_of_column(start_d, D("2026-11-05"), "skills")
        self.assertEqual(idx, 2)

    def test_books_after_flush(self):
        # 清库存会发掉 books 002/003，done.books 记 2；
        # 11-06 是第三个书日，idx 应为 5 —— 已经超出 3 篇，应报「用完」
        start_d = D(send.MANIFEST_DATA["start"])
        done = send.load_progress()
        idx = done.get("books", 0) + send.nth_of_column(start_d, D("2026-11-06"), "books")
        self.assertEqual(idx, 5)


if __name__ == "__main__":
    unittest.main()
