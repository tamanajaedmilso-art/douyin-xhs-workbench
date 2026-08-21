# 抖音/小红书医美+试管婴儿爆款采集工具

用于采集抖音、小红书平台上医美、试管婴儿/备孕赛道爆款内容，自动拆解文案结构，并导出 Excel/CSV。

> ⚠️ **重要提示**
> - 本工具仅抓取平台**公开可见**内容，不爬取隐私数据
> - 抖音/小红书页面结构和反爬策略会不定期变化，遇到采集失败时需要调整 CSS 选择器
> - 自动采集存在账号风控、限流甚至封禁风险，请控制采集频率，建议使用小号测试
> - 请遵守各平台用户协议及相关法律法规

---

## 1. 环境准备

需要安装 Python 3.8+，以及 Playwright 浏览器。

```bash
# 进入爬虫目录
cd crawler

# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器（仅需一次）
playwright install chromium
```

---

## 2. 配置文件说明

`config.json` 是核心配置文件，主要字段：

| 字段 | 说明 |
|------|------|
| `platforms` | 要采集的平台，`["douyin", "xiaohongshu"]` |
| `keywords` | 搜索关键词列表，可自行增删 |
| `category_map` | 关键词 → 赛道标签映射（医美/试管婴儿） |
| `thresholds` | 各平台点赞/评论/收藏/播放量阈值，低于阈值会被过滤 |
| `max_results_per_keyword` | 每个关键词最多采集多少条 |
| `delay` | 请求间隔、滚动停顿时间，值越大越安全 |
| `headless` | `false` 会弹出浏览器（推荐首次登录），`true` 为无头模式 |
| `use_system_chrome` | `true` 使用系统已安装的 Chrome，更容易复用登录态 |
| `persistent_context` | `true` 使用持久化浏览器上下文，登录态保存更稳定 |
| `user_data_dir` | 持久化浏览器配置文件目录 |
| `cookies_dir` | 登录 Cookie 保存目录 |
| `data_dir` | 采集数据保存目录 |
| `output_dir` | Excel/CSV 输出目录 |

---

## 3. 首次登录

抖音和小红书都需要登录后才能稳定搜索。推荐使用专门的登录模式：

```bash
python main.py --login
```

这会弹出你系统里已安装的 Chrome 浏览器，依次打开抖音和小红书登录页。你手动扫码/短信登录完成后，按回车即可。

登录态会保存在 `browser_profile/` 和 `cookies/` 目录，后续运行 `python main.py --run` 会自动复用。

如果 Cookie 过期导致跳到登录页，脚本会暂停并提示你手动登录，按回车继续。

---

## 4. 运行方式

### 4.1 只保存登录态

```bash
python main.py --login
```

### 4.2 手动采集一次

```bash
python main.py --run
```

运行后会：
1. 按 `config.json` 中的关键词逐个搜索
2. 进入每个作品详情页采集完整数据
3. 自动拆解文案结构
4. 增量保存到 `data/collected_items.json`
5. 导出 Excel 和 CSV 到 `output/` 目录

### 4.3 只导出已有数据

```bash
python main.py --export
```

### 4.4 查看采集统计

```bash
python main.py --stats
```

### 4.5 定时每周采集

修改 `config.json` 中的 `schedule` 字段，然后运行：

```bash
python main.py --schedule
```

默认每周一上午 9:00 自动执行一次。

---

## 5. macOS 用户特别提示

如果你在当前这台 Mac 上运行：

1. 确保 `config.json` 中：
   - `"headless": false`（必须，否则看不到浏览器）
   - `"use_system_chrome": true`（使用你刚才登录过的 Chrome）
   - `"persistent_context": true`（保留登录态）

2. 首次运行先登录：
   ```bash
   python main.py --login
   ```

3. 登录成功后，再运行采集：
   ```bash
   python main.py --run
   ```

4. 如果爬虫打开的是全新 Chrome 窗口（没有你的登录态），说明你用的是 Playwright 自带的 Chromium。检查 `use_system_chrome` 是否为 `true`。

---

## 6. 导出字段说明

Excel/CSV 包含以下列：

| 列名 | 说明 |
|------|------|
| 平台 | douyin / xiaohongshu |
| 赛道标签 | 医美 / 试管婴儿 |
| 关键词 | 搜索时使用的关键词 |
| 作品链接 | 原视频/笔记 URL |
| 发布账号 | 作者名称 |
| 发布时间 | 作品发布时间 |
| 点赞数 | 点赞数（已解析 1.2w、3.5万 等） |
| 评论数 | 评论数 |
| 收藏数 | 收藏数 |
| 转发/分享数 | 分享数 |
| 播放量 | 播放量（抖音可能有，小红书为空） |
| 标题 | 作品标题 |
| 完整文案/正文 | 完整视频文案或笔记正文 |
| 钩子/痛点 | 文案结构拆解：开头痛点/钩子 |
| 价值输出 | 文案结构拆解：中间价值/方法 |
| 引导话术 | 文案结构拆解：互动/私信/扣1等引导 |
| 结尾转化 | 文案结构拆解：结尾 CTA |
| 采集时间 | 本工具采集时间 |

---

## 7. 自定义关键词和阈值

编辑 `config.json`：

```json
{
  "keywords": [
    "医美", "抗衰", "水光针", "轮廓固定",
    "试管", "试管婴儿", "备孕", "促排", "移植"
  ],
  "thresholds": {
    "douyin": {
      "likes_min": 5000,
      "comments_min": 100,
      "play_count_min": 50000
    },
    "xiaohongshu": {
      "likes_min": 1000,
      "comments_min": 100,
      "collections_min": 200
    }
  }
}
```

保存后重新运行 `python main.py --run` 即可。

---

## 8. 常见问题

### Q1：运行后浏览器闪退/打不开页面
- 检查是否执行了 `playwright install chromium`
- 把 `config.json` 里的 `headless` 改为 `false`，看报错信息
- 检查网络是否能访问抖音/小红书网页版

### Q2：采集到的数据都是 0 或为空
- 抖音/小红书页面结构可能已更新，需要修改 `scraper/douyin.py` 和 `scraper/xiaohongshu.py` 中的 CSS 选择器
- 打开浏览器开发者工具（F12），找到对应元素的选择器后替换

### Q3：提示需要登录
- 首次运行必须手动登录
- 如果 Cookie 过期，删除 `cookies/` 目录重新登录

### Q4：账号被风控/验证码
- 增大 `delay` 中的间隔时间
- 降低 `max_results_per_keyword`
- 不要频繁运行，建议每周一次

---

## 9. 项目结构

```
crawler/
├── config.json              # 配置文件
├── requirements.txt         # Python 依赖
├── main.py                  # 入口脚本
├── README.md                # 本说明
├── scraper/
│   ├── base.py              # 浏览器基础封装
│   ├── douyin.py            # 抖音采集逻辑
│   └── xiaohongshu.py       # 小红书采集逻辑
├── analyzer.py              # 文案结构拆解
├── exporter.py              # Excel/CSV 导出
├── storage.py               # 数据去重与存储
└── utils.py                 # 工具函数
```

---

## 10. 免责声明

本工具仅供学习研究使用。用户需自行承担因使用本工具产生的全部责任，包括但不限于账号封禁、法律纠纷等。开发者不对任何使用后果负责。
