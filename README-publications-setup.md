# Publications 自动更新说明 / Auto-updating Publications Setup

## 数据来源 / Data source

改用 **ORCID 公开 API**（而不是 Google Scholar 或 ResearchGate）：

- Google Scholar / ResearchGate 都没有官方公开 API，抓取容易被限流或封锁
  （ResearchGate 对自动化抓取尤其严格，经常直接屏蔽云服务器 IP，比如
  GitHub Actions 的 IP）。
- ORCID 提供官方、免费、有文档支持的公开 API，专门为这类程序化访问设计，
  是这三者里唯一不会被限制的来源。

你的 ORCID 记录：https://orcid.org/0000-0001-5389-4157

## 工作原理 / How it works

1. `scripts/fetch_orcid.py` 用 ORCID 公开 API 抓取最新的 10 篇 works，
   写入 `publications.json`。
2. `.github/workflows/update-publications.yml` 大约每 5 天自动运行一次这个脚本，
   并把更新后的 `publications.json` 提交回仓库。
3. `index.html` 加载时用 JavaScript 读取 `publications.json` 渲染 Publications
   列表；加载出来之前，先显示页面里写死的 10 条作为占位/离线兜底内容。

## 你需要做的事 / What you need to do

### 1. 申请 ORCID API 凭证（免费、自助、即时通过）

1. 登录 https://orcid.org
2. 点右上角你的名字 → **Developer Tools**（如果没验证邮箱会提示先验证）
3. 注册一个 Public API client，会得到一个 **Client ID** 和 **Client Secret**
   （立即生效，不需要人工审核）

### 2. 把凭证加到 GitHub 仓库

仓库 Settings → Secrets and variables → Actions → New repository secret，
添加两个：
- `ORCID_CLIENT_ID`
- `ORCID_CLIENT_SECRET`

### 3. 部署这些文件

把下面文件放进你托管网站的 Git 仓库（例如 GitHub Pages）：
- `index.html`（已更新）
- `publications.json`
- `favicon.svg`
- `scripts/fetch_orcid.py`
- `.github/workflows/update-publications.yml`

### 4. 开启工作流写权限

仓库 Settings → Actions → General → Workflow permissions，
选择 **Read and write permissions**，这样定时任务才能把更新后的
`publications.json` 提交回去。

### 5. 测试

推送后去仓库的 Actions 标签页，手动点一次
"Update Publications from ORCID" → "Run workflow" 测试是否成功，
检查 `publications.json` 是否被正确更新提交。

## 重要限制 / Important limitations

- **ORCID 的作者列表并不总是完整的**：这取决于这篇论文的数据是怎么被加进
  ORCID 记录的（自己手动添加、Crossref 自动导入等），有些条目可能没有完整的
  作者名单。脚本已经处理了这种情况——没有作者名单时，网页只显示标题、年份、
  期刊，并直接链接到该论文的 DOI。
- 如果长期抓取失败（比如凭证过期），`publications.json` 会保留上一次成功抓取
  的数据，网站不会因此显示空白。
- 网页用 `fetch()` 读取 `publications.json`，**必须通过 http(s) 访问**
  （比如 GitHub Pages、Netlify，或本地起个简单服务器），直接双击打开
  `index.html`（file:// 协议）无法加载该文件，此时会显示占位内容。

## 自定义图标 / Favicon

`favicon.svg` 是一个简单的鸟形图标占位符，已经在 `index.html` 的 `<head>` 中引用。
你可以直接替换这个文件（保持文件名 `favicon.svg`，或者改名后同步更新
`index.html` 里的 `<link rel="icon" ...>` 路径）。
