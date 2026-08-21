# 抖音&小红书多账号爆款内容工作台

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/tamanajaedmilso-art/douyin-xhs-workbench)

一个专为医美 / 试管备孕 / 个人 IP 运营者设计的内容管理工具。

- **前端**：单个 `index.html`，纯 HTML + Tailwind CSS + JavaScript，数据默认保存在浏览器 `localStorage`。
- **后端（可选）**：Node.js + Express + SQLite，用于接收本地爬虫数据，让网页自动拉取最新爆款模板。
- **爬虫（可选）**：Python + Playwright，自动采集抖音/小红书医美、试管备孕赛道爆款内容。

无需后端也能单独使用；部署后端后可实现「爬虫自动采集 → 网页自动同步」。

---

## 功能概览

1. **多账号管理**
   - 新增、编辑、删除（二次确认弹窗）抖音/小红书账号。
   - 字段：名称、平台、分组、备注、头像。
   - 账号列表支持按平台/分组筛选。
   - 默认内置 5 个示例账号。
   - 创作内容时可勾选分发至一个或多个指定账号。

2. **爆款模板智能解析收纳**
   - 粘贴爆款文案，一键智能解析为：钩子、痛点、痒点、卖点、正文结构、结尾引导、标签。
   - 模板卡片直接展示拆解后的结构要素。
   - 内置 12 条医美/试管备孕爆款模板。
   - 支持收藏、搜索、编辑（完整字段弹窗）、删除、JSON 导入/导出。
   - 模拟“每日自动采集”：首次打开自动生成 2–4 条新模板。

3. **脚本批量生成（核心）**
   - 选择模板 + 输入“新主题/内容中心”。
   - 自动拆解模板底层文案框架（钩子、痛点、痒点、卖点、正文、结尾、标签）。
   - 1:1 复刻结构，将内容替换为新主题，生成差异化文案。
   - 一键切换输出格式：抖音口播稿（口语化、语气词）/ 小红书种草笔记（emoji、分段）。
   - 红色高亮显示违禁词并统计数量。
   - 生成结果可直接复制、保存到素材库或生成分发草稿。

4. **素材资料库**
   - 归档所有生成的脚本。
   - 关键词搜索、详情查看、删除、JSON 导出备份。

6. **草稿分发面板**
   - 从脚本生成或手动创建分发草稿。
   - 选择平台（抖音/小红书/双平台）和目标账号。
   - 状态管理：草稿 / 待拍摄 / 已发布。
   - 一键复制文案到剪贴板。

7. **备份与恢复**
   - 全局导出/导入全部数据。
   - 数据本地存储，所有 key 前缀为 `dwxh_`。

---

## 技术栈

- 前端：HTML5 + Tailwind CSS CDN + 原生 JavaScript（IIFE），数据保存在浏览器 `localStorage`
- 后端：Node.js + Express + SQLite
- 爬虫：Python + Playwright

---

## 文件结构

```
douyin-xhs-workbench/
├── index.html              # 完整的单页应用（HTML + CSS + JS）
├── server.js               # Node.js 后端（Express + SQLite）
├── package.json            # 后端依赖
├── render.yaml             # Render 一键部署配置
├── README.md               # 使用与部署说明
├── vercel.json             # Vercel 部署配置
├── vercel                  # 本地 Vercel CLI 启动脚本
├── crawler/                # Python 爬虫
│   ├── main.py
│   ├── sync.py             # 向后端同步数据
│   ├── config.json         # 关键词、阈值、后端地址等配置
│   └── ...
├── .gitignore              # 忽略 .tools/、data/ 等本地环境
└── .tools/                 # 本地 Node.js + Vercel CLI（自动生成，不提交）
```

---

## 本地使用

1. 直接用浏览器打开 `index.html`。
2. 或者在项目目录运行一个静态服务器：

```bash
cd douyin-xhs-workbench
python3 -m http.server 8080
```

然后访问 `http://localhost:8080`。

---

## 使用项目自带的 Vercel CLI 部署前端（推荐）

项目已内置 Node.js + Vercel CLI，无需你全局安装。

```bash
cd douyin-xhs-workbench

# 1. 登录 Vercel（会提示你打开浏览器授权）
./vercel login

# 2. 部署（首次会引导你选择项目配置，后续直接运行即可）
./vercel --prod
```

部署完成后，Vercel 会给出 `.vercel.app` 公开访问链接。

> `.tools/` 目录是本地 CLI 运行环境，已加入 `.gitignore`，不需要提交到 GitHub。

---

## 后端部署（可选，用于爬虫自动同步）

如果你希望本地爬虫跑完后，网页能自动拉取最新爆款数据，需要部署一个小后端。

### 方案：一键部署到 Render（免费）

1. 访问 GitHub 仓库页面，找到 README 顶部的 **「Deploy to Render」** 按钮。
2. 点击后按提示登录/注册 Render 账号。
3. Render 会自动读取 `render.yaml` 创建 Web Service 和 1GB 磁盘。
4. 部署完成后，Render 会给你类似 `https://douyin-xhs-workbench-backend-xxx.onrender.com` 的域名。
5. 复制这个域名，填入网页「备份/设置」→「后端同步设置」→「后端地址」。
6. 在 Render Dashboard → Environment 里找到 `API_KEY`，复制到网页的「API Key」输入框。
7. 勾选「进入爆款模板时自动同步」，点击「保存配置」。

### 后端环境变量

| 变量 | 说明 | 默认值 |
|---|---|---|
| `API_KEY` | 爬虫推送时必须携带的密钥 | Render 自动生成 |
| `DATA_DIR` | SQLite 数据库目录 | `/var/render/data` |
| `FRONTEND_ORIGINS` | 额外允许的跨域前端域名，逗号分隔 | 空 |
| `PORT` | 服务端口 | 3000 |

### 本地运行后端

```bash
# 安装依赖
npm install

# 启动（默认端口 3000，API_KEY 请自行设置）
API_KEY=your-secret-key npm start

# 开发模式（文件变更自动重启）
API_KEY=your-secret-key npm run dev
```

---

## 爬虫与后端联动

### 1. 配置爬虫

编辑 `crawler/config.json`：

```json
{
  "backend": {
    "url": "https://douyin-xhs-workbench-backend-xxx.onrender.com",
    "api_key": "your-api-key",
    "auto_sync": true
  }
}
```

### 2. 运行采集

```bash
cd crawler
source venv/bin/activate
python main.py --run
```

采集完成后会自动把新增数据推送到后端，同时仍会导出 CSV/Excel 到 `crawler/output/`。

### 3. 只同步本地已有数据到后端

```bash
python main.py --sync-only
```

### 4. 定时每周自动采集

```bash
python main.py --schedule
```

默认每周一 09:00 自动采集并同步。

---

## 备份与导入

### 备份全部数据

1. 进入左侧菜单「备份/设置」。
2. 点击「备份全部数据」，浏览器会下载一个 JSON 文件。

### 导入备份

1. 进入「备份/设置」。
2. 点击「选择备份文件」，选择之前下载的 JSON。
3. 导入成功后所有账号、模板、脚本、草稿会恢复。

### 单独导入/导出模板

在「爆款模板」页面可直接导出模板 JSON，也可导入外部模板文件。

---

## 部署到 GitHub Pages

1. 在 GitHub 创建新仓库，例如 `douyin-xhs-workbench`。
2. 将本仓库代码推送到 GitHub：

```bash
git init
git add index.html README.md vercel.json
git commit -m "init"
git branch -M main
git remote add origin https://github.com/你的用户名/douyin-xhs-workbench.git
git push -u origin main
```

3. 打开仓库页面 → Settings → Pages。
4. Source 选择「Deploy from a branch」，Branch 选择 `main` / `root`。
5. 保存后等待 1–2 分钟，GitHub 会给出访问链接，例如：

```
https://你的用户名.github.io/douyin-xhs-workbench/
```

---

## 部署到 Vercel

1. 将代码推送到 GitHub 仓库（同上）。
2. 访问 [vercel.com](https://vercel.com) 并登录。
3. 点击「Add New Project」，导入 `douyin-xhs-workbench` 仓库。
4. Framework Preset 选择 **Other**（因为是纯静态文件）。
5. 点击 Deploy。

项目已包含 `vercel.json` 配置，Vercel 会自动识别并应用：

```json
{
  "version": 2,
  "public": true,
  "routes": [
    { "src": "/(.*)", "dest": "/index.html" }
  ]
}
```

6. 部署完成后，Vercel 会分配一个 `.vercel.app` 域名，例如：

```
https://douyin-xhs-workbench.vercel.app
```

---

## 注意事项

- 默认情况下，所有数据保存在当前浏览器的 `localStorage` 中，清理浏览器数据会导致丢失，请定期备份。
- 部署后端后，爬虫采集的公开数据会推送到你自己的后端服务器；前端打开时会从该后端拉取，不会上传到第三方。
- 免费 Render 后端会在 15 分钟无访问后休眠，首次访问可能需要等待 30 秒左右唤醒。
- 封面生成使用 HTML Canvas，建议在桌面浏览器使用以获得最佳体验。
- 爬虫仅采集平台公开可见内容，请遵守各平台规则与相关法律法规。

---

## License

MIT
