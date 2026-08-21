require('dotenv').config();
const express = require('express');
const cors = require('cors');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const fs = require('fs');

const app = express();
const PORT = process.env.PORT || 3000;
const API_KEY = process.env.API_KEY || 'changeme';

// 允许的前端域名（本地开发 + 已部署的 Vercel / GitHub Pages）
const ALLOWED_ORIGINS = [
  'http://localhost:8080',
  'http://localhost:3000',
  'http://127.0.0.1:8080',
  'https://douyin-xhs-workbench.vercel.app',
  'https://douyin-xhs-workbench-ldalxhxgn-tamanajaedmilso-9553s-projects.vercel.app',
  'https://tamanajaedmilso-art.github.io',
  'https://tamanajaedmilso-art.github.io/douyin-xhs-workbench',
];

app.use(cors({
  origin: function (origin, callback) {
    if (!origin || ALLOWED_ORIGINS.includes(origin)) {
      callback(null, true);
    } else {
      console.warn('[cors] blocked origin:', origin);
      callback(null, false);
    }
  },
  methods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization'],
}));

app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// 确保数据目录存在
const DATA_DIR = process.env.DATA_DIR || path.join(__dirname, 'data');
if (!fs.existsSync(DATA_DIR)) fs.mkdirSync(DATA_DIR, { recursive: true });
const DB_PATH = path.join(DATA_DIR, 'backend.sqlite');

// 初始化数据库
const db = new sqlite3.Database(DB_PATH, (err) => {
  if (err) {
    console.error('[db] 数据库打开失败:', err.message);
    process.exit(1);
  }
  console.log('[db] 已连接:', DB_PATH);
});

db.serialize(() => {
  db.run(`
    CREATE TABLE IF NOT EXISTS collected_items (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      platform TEXT NOT NULL,
      category TEXT,
      keyword TEXT,
      url TEXT UNIQUE NOT NULL,
      title TEXT,
      author TEXT,
      published_at TEXT,
      likes INTEGER DEFAULT 0,
      comments INTEGER DEFAULT 0,
      collections INTEGER DEFAULT 0,
      shares INTEGER DEFAULT 0,
      play_count INTEGER DEFAULT 0,
      content TEXT,
      hook_pain TEXT,
      value_output TEXT,
      guidance TEXT,
      ending TEXT,
      structure_json TEXT,
      collected_at TEXT NOT NULL,
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
  `);
  db.run(`CREATE INDEX IF NOT EXISTS idx_collected_at ON collected_items(collected_at)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_platform ON collected_items(platform)`);
  db.run(`CREATE INDEX IF NOT EXISTS idx_category ON collected_items(category)`);
});

// 健康检查
app.get('/api/health', (req, res) => {
  db.get('SELECT COUNT(*) as count FROM collected_items', (err, row) => {
    if (err) return res.status(500).json({ ok: false, error: err.message });
    res.json({ ok: true, count: row.count, time: new Date().toISOString() });
  });
});

// 查询采集数据（支持过滤、分页）
app.get('/api/items', (req, res) => {
  const { platform, category, keyword, limit = 100, offset = 0 } = req.query;
  let sql = 'SELECT * FROM collected_items WHERE 1=1';
  const params = [];
  if (platform) { sql += ' AND platform = ?'; params.push(platform); }
  if (category) { sql += ' AND category = ?'; params.push(category); }
  if (keyword) { sql += ' AND keyword = ?'; params.push(keyword); }
  sql += ' ORDER BY collected_at DESC LIMIT ? OFFSET ?';
  params.push(parseInt(limit) || 100, parseInt(offset) || 0);

  db.all(sql, params, (err, rows) => {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ items: rows.map(rowToItem) });
  });
});

// 增量同步：返回 since 时间之后的数据
app.get('/api/items/latest', (req, res) => {
  const since = req.query.since || '1970-01-01T00:00:00.000Z';
  db.all(
    'SELECT * FROM collected_items WHERE collected_at > ? ORDER BY collected_at DESC',
    [since],
    (err, rows) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ items: rows.map(rowToItem), since });
    }
  );
});

// 批量新增/更新（需要 API Key）
app.post('/api/items/batch', (req, res) => {
  const { items, api_key } = req.body;
  if (api_key !== API_KEY) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  if (!Array.isArray(items) || items.length === 0) {
    return res.status(400).json({ error: 'items must be a non-empty array' });
  }

  const stmt = db.prepare(`
    INSERT INTO collected_items
    (platform, category, keyword, url, title, author, published_at, likes, comments, collections, shares, play_count, content, hook_pain, value_output, guidance, ending, structure_json, collected_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(url) DO UPDATE SET
      title=excluded.title,
      author=excluded.author,
      published_at=excluded.published_at,
      likes=excluded.likes,
      comments=excluded.comments,
      collections=excluded.collections,
      shares=excluded.shares,
      play_count=excluded.play_count,
      content=excluded.content,
      hook_pain=excluded.hook_pain,
      value_output=excluded.value_output,
      guidance=excluded.guidance,
      ending=excluded.ending,
      structure_json=excluded.structure_json,
      category=excluded.category,
      keyword=excluded.keyword,
      collected_at=excluded.collected_at,
      updated_at=CURRENT_TIMESTAMP
  `);

  let inserted = 0;
  let updated = 0;
  let failed = 0;

  db.serialize(() => {
    items.forEach((item) => {
      const url = item.url || item.sourceLink || '';
      if (!url) { failed++; return; }
      const structure = item.structure || {};
      stmt.run([
        item.platform || '',
        item.category || '',
        item.keyword || '',
        url,
        item.title || '',
        item.author || '',
        item.published_at || '',
        item.likes || 0,
        item.comments || 0,
        item.collections || 0,
        item.shares || 0,
        item.play_count || 0,
        item.content || '',
        structure.hook_pain || item.hook_pain || '',
        structure.value_output || item.value_output || '',
        structure.guidance || item.guidance || '',
        structure.ending || item.ending || '',
        JSON.stringify(structure),
        item.collected_at || new Date().toISOString(),
      ], function (err) {
        if (err) {
          console.error('[batch] insert/update failed:', err.message);
          failed++;
        } else if (this.changes === 1) {
          // 无法直接区分 insert 与 update，简单按总数处理
        }
      });
    });
    stmt.finalize((err) => {
      if (err) return res.status(500).json({ error: err.message });
      res.json({ ok: true, received: items.length, failed });
    });
  });
});

// 删除单条
app.delete('/api/items/:id', (req, res) => {
  const { api_key } = req.body || {};
  if (api_key !== API_KEY) {
    return res.status(401).json({ error: 'Invalid API key' });
  }
  db.run('DELETE FROM collected_items WHERE id = ?', [req.params.id], function (err) {
    if (err) return res.status(500).json({ error: err.message });
    res.json({ ok: true, deleted: this.changes });
  });
});

function rowToItem(row) {
  return {
    id: row.id,
    platform: row.platform,
    category: row.category,
    keyword: row.keyword,
    url: row.url,
    title: row.title,
    author: row.author,
    published_at: row.published_at,
    likes: row.likes,
    comments: row.comments,
    collections: row.collections,
    shares: row.shares,
    play_count: row.play_count,
    content: row.content,
    hook_pain: row.hook_pain,
    value_output: row.value_output,
    guidance: row.guidance,
    ending: row.ending,
    structure: safeJsonParse(row.structure_json),
    collected_at: row.collected_at,
    created_at: row.created_at,
    updated_at: row.updated_at,
  };
}

function safeJsonParse(str) {
  try { return JSON.parse(str); } catch (e) { return {}; }
}

// 根路由：简单提示
app.get('/', (req, res) => {
  res.json({
    name: '抖音&小红书爆款内容工作台后端',
    status: 'ok',
    endpoints: ['/api/health', '/api/items', '/api/items/latest', '/api/items/batch'],
  });
});

app.listen(PORT, () => {
  console.log(`[server] 后端已启动: http://localhost:${PORT}`);
  console.log(`[server] API Key: ${API_KEY === 'changeme' ? '未设置，请尽快设置 API_KEY 环境变量' : '已设置'}`);
});
