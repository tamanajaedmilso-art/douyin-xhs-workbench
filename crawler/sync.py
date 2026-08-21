import json
from typing import Any, Dict, List

import requests


def push_items(items: List[Dict[str, Any]], config: Dict[str, Any], logger) -> Dict[str, Any]:
    """把采集到的数据推送到后端服务器"""
    backend_url = config.get("backend", {}).get("url", "").rstrip("/")
    api_key = config.get("backend", {}).get("api_key", "")

    if not backend_url:
        logger.warning("[sync] 未配置 backend.url，跳过同步")
        return {"ok": False, "error": "backend.url not configured"}
    if not api_key:
        logger.warning("[sync] 未配置 backend.api_key，跳过同步")
        return {"ok": False, "error": "backend.api_key not configured"}

    url = f"{backend_url}/api/items/batch"
    payload = {
        "items": items,
        "api_key": api_key,
    }

    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        logger.info(f"[sync] 已推送 {len(items)} 条到后端，结果: {data}")
        return data
    except requests.exceptions.RequestException as e:
        logger.error(f"[sync] 推送到后端失败: {e}")
        return {"ok": False, "error": str(e)}


def push_storage(storage, config: Dict[str, Any], logger) -> Dict[str, Any]:
    """把 Storage 中全部 items 推送到后端"""
    return push_items(storage.items, config, logger)
