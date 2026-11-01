# 每日一条 · 推送仓库

这个仓库只做一件事：**每天北京时间 12:30，把 `articles/` 里的一篇文章推到你的手机**（通过 PushPlus）。

## 目录结构

```
.
├─ .github/
│  ├─ send.py                     # 干活的脚本：选出今天的文章并发送
│  └─ workflows/daily.yml         # 定时触发器
├─ articles/
│  ├─ 001-野生蘑菇.md
│  └─ ...                         # 按文件名排序，第 N 天发第 N 篇
└─ README.md
```

## 一次性配置（5 步）

### 1. 拿到 PushPlus token

1. 手机微信扫码登录 <https://www.pushplus.plus>
2. 进入「一对一消息」页面，复制 **token**（一串字母数字）

### 2. 先单独测一次推送

在本机 PowerShell 跑（把 token 换成你自己的）：

```powershell
$body = @{
  token    = "你的token"
  title    = "推送通道测试"
  content  = "看到这条说明链路通了。"
  template = "html"
} | ConvertTo-Json

Invoke-RestMethod -Uri 'http://api.pushplus.plus/send' -Method Post -Body $body -ContentType 'application/json'
```

返回 `code : 200` 且手机收到，才继续往下走。

### 3. 建 GitHub 仓库

1. 打开 <https://github.com/new>
2. 仓库名随意，例如 `daily-life`
3. **选 Private**（内容虽然是公开书稿的改写，但私有更省心）
4. 不要勾选任何初始化文件，直接 Create

### 4. 上传这些文件

网页方式（本机没装 git，用这个最简单）：

1. 仓库页点 **Add file → Upload files**
2. 把 `articles/` 整个文件夹拖进去 → Commit
3. 再点 **Add file → Create new file**，文件名填 `.github/send.py`，把本地的 `send.py` 内容粘贴进去
4. 同样方式建 `.github/workflows/daily.yml`

> 注意：`.github` 开头的文件夹在网页上没法直接拖拽，必须用「Create new file」并在文件名里打斜杠来创建。

### 5. 配置 secret

1. 仓库 **Settings → Secrets and variables → Actions**
2. 点 **New repository secret**
3. Name 填 `PUSHPLUS_TOKEN`，Secret 填你的 token
4. 保存

### 6. 手动跑一次

仓库 **Actions** 标签页 → 左侧「每日一条」→ 右侧 **Run workflow** → 绿色按钮。

约 30 秒后刷新，应看到绿色对勾，手机收到第 1 篇。

---

## 已知限制

| 项 | 说明 |
|---|---|
| 延迟 | GitHub 定时任务常延迟 5–30 分钟，12:30 的推送可能 12:45 才到 |
| 自动停用 | 仓库连续 **60 天没有提交**，GitHub 会自动停用定时任务。届时随便手动跑一次即可恢复 |
| 内容上限 | PushPlus 单条正文有长度限制，目前每篇 300–500 字远低于上限 |
| 免费额度 | 公开仓库 Actions 完全免费；私有仓库每月 2000 分钟，这个用量每天约 1 分钟，够用 |

## 改内容

- 加文章：往 `articles/` 里放 `002-xxx.md`、`003-xxx.md`……文件名排序即推送顺序
- 第一篇标题取自文件第一行（`# ` 开头的行），正文是其余全部
- 改起始日期：编辑 `daily.yml` 里的 `START_DATE`
- 想重发某一天：临时把 `send.py` 的 `FORCE_INDEX` 环境变量设成篇号
