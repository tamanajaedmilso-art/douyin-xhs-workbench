import json
import logging
import os
import random
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


def setup_logging(level: str = "INFO") -> logging.Logger:
    """配置日志输出"""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    return logging.getLogger("crawler")


def load_config(path: str = "config.json") -> Dict[str, Any]:
    """加载 JSON 配置文件"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dirs(dirs: List[str]) -> None:
    """确保目录存在"""
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)


def random_delay(min_seconds: float, max_seconds: float) -> None:
    """随机等待，模拟人类操作间隔"""
    time.sleep(random.uniform(min_seconds, max_seconds))


def human_scroll(page, scroll_count: int = 3, min_pause: float = 1.0, max_pause: float = 3.0) -> None:
    """模拟人类滚动页面"""
    for _ in range(scroll_count):
        # 随机滚动距离
        distance = random.randint(400, 1000)
        page.evaluate(f"window.scrollBy(0, {distance})")
        random_delay(min_pause, max_pause)


def parse_count(text: Optional[str]) -> int:
    """
    把点赞/评论/收藏文本转成数字
    支持：1.2w、3.5万、1.5k、1234、1.2w+
    """
    if text is None:
        return 0
    text = str(text).strip().replace(",", "").replace("+", "")
    if not text:
        return 0
    match = re.match(r"^(\d+(\.\d+)?)\s*([wW万kK千]?)\s*$", text)
    if not match:
        # 尝试直接提取数字
        nums = re.findall(r"\d+", text)
        return int(nums[0]) if nums else 0
    num, _, unit = match.groups()
    num = float(num)
    if unit in ("w", "W", "万"):
        return int(num * 10000)
    if unit in ("k", "K", "千"):
        return int(num * 1000)
    return int(num)


def sanitize_filename(name: str) -> str:
    """把字符串转为安全文件名"""
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip() or "unknown"


def extract_number(text: str) -> Optional[int]:
    """从文本中提取第一个整数"""
    nums = re.findall(r"\d+", str(text))
    return int(nums[0]) if nums else None


def now_str(fmt: str = "%Y%m%d_%H%M%S") -> str:
    """当前时间字符串"""
    from datetime import datetime
    return datetime.now().strftime(fmt)


def load_json(path: str) -> List[Dict[str, Any]]:
    """加载 JSON 数据文件"""
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: str, data: Any) -> None:
    """保存 JSON 数据文件"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def normalize_url(url: str) -> str:
    """规范化 URL，去掉多余参数"""
    if not url:
        return ""
    if url.startswith("//"):
        url = "https:" + url
    return url.split("?")[0].rstrip("/")


def truncate_text(text: str, max_len: int = 500) -> str:
    """截断文本"""
    if not text:
        return ""
    return text[:max_len] + ("..." if len(text) > max_len else "")
