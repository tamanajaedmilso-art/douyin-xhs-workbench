import hashlib
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from utils import ensure_dirs, load_json, now_str, save_json


class Storage:
    """本地数据存储：增量采集、去重、持久化"""

    def __init__(self, data_dir: str = "./data"):
        self.data_dir = Path(data_dir)
        ensure_dirs([str(self.data_dir)])
        self.items_file = self.data_dir / "collected_items.json"
        self.seen_file = self.data_dir / "seen_urls.json"
        self.items: List[Dict[str, Any]] = load_json(str(self.items_file))
        self.seen_urls: Dict[str, str] = load_json(str(self.seen_file))

    def _url_hash(self, url: str) -> str:
        """对 URL 做哈希，作为去重 key"""
        return hashlib.md5(url.encode("utf-8")).hexdigest()

    def exists(self, url: str) -> bool:
        """判断某条 URL 是否已采集"""
        return self._url_hash(url) in self.seen_urls

    def add(self, item: Dict[str, Any]) -> bool:
        """
        添加一条采集结果，重复则跳过。
        返回 True 表示新增，False 表示已存在。
        """
        url = item.get("url", "")
        if not url:
            return False
        key = self._url_hash(url)
        if key in self.seen_urls:
            return False
        item["collected_at"] = datetime.now().isoformat()
        self.items.append(item)
        self.seen_urls[key] = item.get("published_at", "") or datetime.now().isoformat()
        return True

    def add_batch(self, items: List[Dict[str, Any]]) -> int:
        """批量添加，返回新增数量"""
        added = 0
        for item in items:
            if self.add(item):
                added += 1
        return added

    def save(self) -> None:
        """持久化到本地"""
        save_json(str(self.items_file), self.items)
        save_json(str(self.seen_file), self.seen_urls)

    def query(self, platform: str = None, keyword: str = None, category: str = None) -> List[Dict[str, Any]]:
        """按条件筛选已采集数据"""
        result = self.items
        if platform:
            result = [x for x in result if x.get("platform") == platform]
        if keyword:
            result = [x for x in result if keyword in (x.get("keyword") or "")]
        if category:
            result = [x for x in result if x.get("category") == category]
        return result

    def latest_batch_id(self) -> str:
        """生成本次采集批次号"""
        return now_str("%Y%m%d_%H%M%S")

    def stats(self) -> Dict[str, int]:
        """统计各平台数量"""
        stats = {"total": len(self.items), "douyin": 0, "xiaohongshu": 0}
        for item in self.items:
            p = item.get("platform")
            if p in stats:
                stats[p] += 1
        return stats
