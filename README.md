# 每日快报 · 发布仓库

每天推送一条短文到微信，并同步到一个可装到手机主屏幕的网页版。

## 内容分三条线

| 栏目 | 目录 | 排期 | 推送时间 |
|---|---|---|---|
| 书 | `articles/books/` | 周一 / 周三 / 周五 | 12:30 |
| 技能 | `articles/skills/` | 周二 / 周四 | 12:30 |
| 周报 | `articles/weekly/` | 周六 | **08:30** |
| — | — | 周日不发 | — |

栏目内**按文件名排序**，第 N 次推送取第 N 个文件。文件名建议 `001-hl-标题.md` 这种形式，`hl` 是书名标记，方便一眼看出这篇来自哪本书。

## 目录结构

```
.
├─ articles/
│  ├─ books/      书线
│  ├─ skills/     技能线
│  └─ weekly/     周报
├─ web/           template.html（页面模板）/ build_site.py（编译脚本）
├─ docs/          编译产物 = GitHub Pages 发布目录（不要手改）
├─ .github/
│  ├─ send.py     选栏目 + 选篇 + 推送
│  ├─ alert.py    失败告警
│  └─ workflows/
│     ├─ daily.yml    每天 12:30
│     ├─ weekly.yml   周六 08:30
│     └─ build.yml    有新 .md 就自动重建 docs/
└─ README.md
```

## 一次性配置

1. 在 <https://sct.ftqq.com> 微信扫码，拿 `SCT` 开头的 SendKey，并关注它的服务号（不关注收不到）
2. 仓库 **Settings → Secrets and variables → Actions** 新建 secret：`SERVERCHAN_SENDKEY`
3. **Settings → Pages**：Branch `main` + 文件夹 `/docs`
4. **Actions** 里手动跑一次「每日一条」验证

## 日常怎么加内容

只需要把 `.md` 放进对应栏目目录，推上去即可——`build.yml` 会自动重建站点，不用手改 `docs/`。

文章格式：

```
# 标题（第一行，# 后有空格）

正文段落，空行分隔。**加粗**是关键数字。

---

<sub>出处：第 X 节第 Y 条 · 证据 A · 来源</sub>
```

## 三个保险

| 保险 | 行为 |
|---|---|
| 库存预警 | 该栏目剩余不足 3 篇时，推送末尾自动提醒 |
| 断更保护 | 该栏目稿件用完时，**不发旧文**，改发一条「稿件已用完」提醒 |
| 失败告警 | 工作流失败时自动推一条微信告警，不会静默失败 |

## 手动排查

```bash
# 只看今天会发什么，不发出去
DRY_RUN=1 python3 .github/send.py

# 假装今天是某个日期（验证排期）
DRY_RUN=1 FORCE_DATE=2026-11-07 python3 .github/send.py
```
