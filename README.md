# 每日一条 · 推送仓库

这个仓库只做一件事：**每天北京时间 12:30，把 `articles/` 里的一篇文章推到你的手机**。

推送走 **Server酱 Turbo**（微信服务号接收，免费每天 5 条，不需要实名和付费）。

## 目录结构

```
.
├─ .github/
│  ├─ send.py                     # 干活的脚本：选出今天的文章并发送
│  └─ workflows/
│     ├─ daily.yml                # 每天 12:30 定时推送
│     └─ build.yml                # 有新的 .md 就自动重建 docs/
├─ articles/
│  ├─ 001-野生蘑菇.md
│  └─ ...                         # 按文件名排序，第 N 天发第 N 篇
├─ web/                           # 站点源码（template.html / build_site.py）
├─ docs/                          # 编译产物 = GitHub Pages 发布目录
└─ README.md
```

## 一次性配置（6 步）

### 1. 拿到 Server酱 SendKey

1. 浏览器打开 <https://sct.ftqq.com>
2. **手机微信扫码**登录
3. 进「SendKey」页面，复制 `SCT` 开头的那串
4. 按页面提示关注它的微信服务号——**不关注收不到消息**

### 2. 先单独测一次推送

打开 PowerShell（`Win+R` → `powershell`），粘贴：

```powershell
[Net.ServicePointManager]::SecurityProtocol = 'Tls12'
$key = "你复制的SCT开头key"
Invoke-RestMethod -Uri "https://sctapi.ftqq.com/$key.send" -Method Post -Body @{title="link test"; desp="channel ok"}
```

返回 `code : 0` 且手机微信收到，才继续往下走。

> 测试内容故意用英文：Windows PowerShell 5.1 发中文表单会乱码。真实推送跑在 GitHub 的 Linux 环境里，中文正常。

### 3. 建 GitHub 仓库

1. 打开 <https://github.com/new>
2. 仓库名随意，例如 `daily-life`
3. 公开仓库可直接用 Pages；私有仓库需要 Pro（学生包可免费拿）
4. 不要勾选任何初始化文件，直接 Create

### 4. 上传这些文件

网页方式（本机没装 git，用这个最简单）：

1. 仓库页点 **Add file → Upload files**
2. 把 `articles/`、`docs/`、`web/` 三个文件夹和 `README.md` 拖进去 → Commit
3. 再点 **Add file → Create new file**，文件名填 `.github/send.py`，把本地的 `send.py` 内容粘贴进去
4. 同样方式建 `.github/workflows/daily.yml`

> 注意：`.github` 开头的文件夹在网页上没法直接拖拽，必须用「Create new file」并在文件名里打斜杠来创建。

### 5. 配置 secret

1. 仓库 **Settings → Secrets and variables → Actions**
2. 点 **New repository secret**
3. Name 填 `SERVERCHAN_SENDKEY`，Secret 填你的 SendKey
4. 保存

### 6. 手动跑一次

仓库 **Actions** 标签页 → 左侧「每日一条」→ 右侧 **Run workflow** → 绿色按钮。

约 30 秒后刷新，应看到绿色对勾，手机收到第 1 篇。

### 7. 开启网页版（可选）

**Settings → Pages** → Source 选 `Deploy from a branch` → Branch 选 `main` + 文件夹选 **`/docs`** → Save。

一两分钟后得到 `https://<用户名>.github.io/daily-life/`，手机浏览器打开后可「添加到主屏幕」，全屏无地址栏、离线可读。

---

## 已知限制

| 项 | 说明 |
|---|---|
| 延迟 | GitHub 定时任务常延迟 5–30 分钟，12:30 的推送可能 12:45 才到 |
| 自动停用 | 仓库连续 **60 天没有提交**，GitHub 会自动停用定时任务。届时随便手动跑一次即可恢复 |
| 免费额度 | Server酱 免费会员每天 5 条，本项目每天只用 1 条 |
| 消息格式 | Server酱 的正文只支持 **Markdown**，不支持 HTML。`send.py` 已按 Markdown 生成 |
| 保留时间 | Server酱 免费版服务端只保留 1 天；手机上收到后内容留在微信里，不受影响 |
| 内容上限 | 每篇 300–500 字，远低于任何长度限制 |

## 备用通道：pushplus

如果哪天 Server酱 不可用，`send.py` 里保留了 pushplus 分支：只要把 secret 名改成 `PUSHPLUS_TOKEN` 并删掉 `SERVERCHAN_SENDKEY`，脚本会自动切过去。

注意 pushplus **现在要求完成实名认证**（第三方核验，¥3.9 一次性，或 ¥10 开会员），未实名时接口返回 `code 905`，发不出任何消息。

## 改内容

- **加文章：只需要往 `articles/` 里传那一个 `.md` 文件**，`build.yml` 会自动重跑 `build_site.py` 并把 `docs/` 提交回仓库（约 1 分钟）。不用再手工传 `index.html`
- 文件名排序即推送顺序：`002-xxx.md` 是第 2 天、`003-xxx.md` 是第 3 天
- 每篇标题取自文件第一行（`# ` 开头的行），正文是其余全部，末尾 `<sub>…</sub>` 是出处角标
- 改起始日期：编辑 `daily.yml` 里的 `START_DATE`，同时改 `web/build_site.py` 里的 `START_DATE`（两处必须一致）
- 想重发某一天：把 `send.py` 的 `FORCE_INDEX` 环境变量设成篇号
- 想只预览不发送：设置 `DRY_RUN=1`，脚本会打印将要发送的标题、字数、出处和完整正文
