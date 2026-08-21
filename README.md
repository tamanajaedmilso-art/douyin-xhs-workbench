# 抖音&小红书多账号爆款内容工作台

一个专为医美 / 试管备孕 / 个人 IP 运营者设计的静态内容管理工具。无需后端、无需构建，单个 HTML 文件即可运行，数据完全保存在浏览器 `localStorage` 中。

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

- HTML5 + Tailwind CSS CDN
- Google Fonts：Noto Sans SC
- Lucide Icons CDN
- 原生 JavaScript（IIFE），全局暴露 `app` 对象
- 浏览器 localStorage 持久化

---

## 文件结构

```
douyin-xhs-workbench/
├── index.html   # 完整的单页应用（HTML + CSS + JS）
├── README.md    # 使用与部署说明
├── vercel.json  # Vercel 部署配置
├── vercel       # 本地 Vercel CLI 启动脚本
├── .gitignore   # 忽略 .tools/ 等本地环境
└── .tools/      # 本地 Node.js + Vercel CLI（自动生成，不提交）
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

## 使用项目自带的 Vercel CLI 部署（推荐）

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

- 所有数据保存在当前浏览器的 `localStorage` 中，清理浏览器数据会导致丢失，请定期备份。
- 本项目为纯前端工具，不会上传任何数据到服务器。
- 封面生成使用 HTML Canvas，建议在桌面浏览器使用以获得最佳体验。

---

## License

MIT
