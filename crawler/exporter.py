import csv
import os
from pathlib import Path
from typing import Any, Dict, List

from utils import ensure_dirs, now_str, sanitize_filename


class Exporter:
    """导出 Excel/CSV"""

    def __init__(self, output_dir: str = "./output"):
        self.output_dir = Path(output_dir)
        ensure_dirs([str(self.output_dir)])

    def _flatten_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """把 item + structure 展开成平铺字段"""
        structure = item.get("structure", {})
        return {
            "平台": item.get("platform", ""),
            "赛道标签": item.get("category", ""),
            "关键词": item.get("keyword", ""),
            "作品链接": item.get("url", ""),
            "发布账号": item.get("author", ""),
            "发布时间": item.get("published_at", ""),
            "点赞数": item.get("likes", 0),
            "评论数": item.get("comments", 0),
            "收藏数": item.get("collections", 0),
            "转发/分享数": item.get("shares", 0),
            "播放量": item.get("play_count", 0),
            "标题": item.get("title", ""),
            "完整文案/正文": item.get("content", ""),
            "钩子/痛点": structure.get("hook_pain", ""),
            "价值输出": structure.get("value_output", ""),
            "引导话术": structure.get("guidance", ""),
            "结尾转化": structure.get("ending", ""),
            "采集时间": item.get("collected_at", ""),
        }

    def to_csv(self, items: List[Dict[str, Any]], filename: str = None) -> str:
        """导出 CSV，返回文件路径"""
        if not items:
            return ""
        if filename is None:
            filename = f"collected_{now_str()}.csv"
        path = self.output_dir / filename
        fieldnames = list(self._flatten_item(items[0]).keys())
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for item in items:
                writer.writerow(self._flatten_item(item))
        return str(path)

    def to_excel(self, items: List[Dict[str, Any]], filename: str = None) -> str:
        """导出 Excel，多 sheet：汇总、抖音、小红书"""
        if not items:
            return ""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("导出 Excel 需要 pandas 和 openpyxl，请先安装依赖")

        if filename is None:
            filename = f"collected_{now_str()}.xlsx"
        path = self.output_dir / filename

        all_rows = [self._flatten_item(item) for item in items]
        df_all = pd.DataFrame(all_rows)
        df_douyin = pd.DataFrame([r for r in all_rows if r.get("平台") == "douyin"])
        df_xhs = pd.DataFrame([r for r in all_rows if r.get("平台") == "xiaohongshu"])

        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df_all.to_excel(writer, sheet_name="汇总", index=False)
            if not df_douyin.empty:
                df_douyin.to_excel(writer, sheet_name="抖音", index=False)
            if not df_xhs.empty:
                df_xhs.to_excel(writer, sheet_name="小红书", index=False)

        return str(path)

    def export_by_platform(self, items: List[Dict[str, Any]], fmt: str = "both") -> Dict[str, str]:
        """按平台分别导出，返回文件路径字典"""
        results = {}
        if fmt in ("csv", "both"):
            results["csv"] = self.to_csv(items)
        if fmt in ("xlsx", "excel", "both"):
            results["xlsx"] = self.to_excel(items)
        return results
