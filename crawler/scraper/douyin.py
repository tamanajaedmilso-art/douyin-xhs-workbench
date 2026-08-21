import re
import time
from typing import Any, Dict, List

from playwright.sync_api import TimeoutError as PlaywrightTimeout

from utils import human_scroll, parse_count, truncate_text
from .base import BaseScraper


class DouyinScraper(BaseScraper):
    """抖音爬虫（网页版）

    注意：抖音网页结构变化频繁，若采集失败请按实际页面调整 CSS 选择器。
    """

    BASE_URL = "https://www.douyin.com"

    def __init__(self, config: Dict[str, Any], logger):
        super().__init__("douyin", config, logger)
        self.thresholds = config.get("thresholds", {}).get("douyin", {})

    def search(self, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """按关键词搜索抖音视频"""
        self.logger.info(f"[douyin] 开始搜索关键词: {keyword}")
        search_url = f"{self.BASE_URL}/search/{keyword}?type=video"
        if not self.safe_goto(search_url):
            # 重试一次，有时页面加载慢
            self.logger.warning(f"[douyin] 第一次搜索失败，3 秒后重试...")
            time.sleep(3)
            if not self.safe_goto(search_url):
                return []

        # 等待页面加载，必要时过登录/验证
        time.sleep(3)
        self.wait_for_manual_login()

        results = []
        seen_urls = set()
        attempts = 0
        while len(results) < max_results and attempts < max_results // 3 + 5:
            # 提取当前页面视频卡片
            cards = self._extract_video_cards()
            for card in cards:
                url = card.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(card)
                if len(results) >= max_results:
                    break
            # 滚动加载更多
            self.human_scroll(count=2)
            attempts += 1

        self.logger.info(f"[douyin] 关键词 [{keyword}] 搜索到 {len(results)} 条结果")

        # 进入详情页补全数据
        detailed = []
        for i, card in enumerate(results[:max_results]):
            try:
                self.logger.info(f"[douyin] 正在采集第 {i+1}/{len(results[:max_results])} 条详情: {card.get('url')}")
                detail = self.parse_detail(card["url"])
                card.update(detail)
                if self._pass_threshold(card):
                    card["keyword"] = keyword
                    card["platform"] = "douyin"
                    detailed.append(card)
                    self.logger.info(f"[douyin] 采集成功: {card.get('title', '')[:30]}，点赞 {card.get('likes', 0)}")
                else:
                    self.logger.info(f"[douyin] 未通过阈值过滤: {card.get('title', '')[:30]}")
                self.random_wait()
            except Exception as e:
                self.logger.error(f"[douyin] 详情页采集失败: {card.get('url')}, {e}")
        return detailed

    def _extract_video_cards(self) -> List[Dict[str, Any]]:
        """从搜索结果页提取视频卡片"""
        cards = []
        # 抖音搜索页卡片选择器（可能变化）
        selectors = [
            'a[href*="/video/"]',
            '[data-e2e="search-card-video"] a',
            '.search-card-video a',
        ]
        elements = []
        for sel in selectors:
            try:
                elements = self.page.query_selector_all(sel)
                if elements:
                    break
            except Exception:
                continue

        for el in elements:
            try:
                href = el.get_attribute("href") or ""
                if href.startswith("//"):
                    href = "https:" + href
                elif not href.startswith("http"):
                    href = self.BASE_URL + href
                if "/video/" not in href:
                    continue
                # 提取 video id，统一用标准详情页
                m = re.search(r"/video/(\d+)", href)
                if not m:
                    continue
                video_id = m.group(1)
                clean_url = f"https://www.douyin.com/video/{video_id}"
                title_el = el.query_selector("span, .title, [class*='title']")
                title = title_el.inner_text() if title_el else ""
                cards.append({"url": clean_url, "title": truncate_text(title, 200)})
            except Exception:
                continue
        return cards

    def parse_detail(self, url: str) -> Dict[str, Any]:
        """进入视频详情页采集完整信息。抖音详情页数据主要在 title 和 meta description 里。"""
        if not self.safe_goto(url):
            return {}
        time.sleep(3)

        data = {
            "content": "",
            "author": "",
            "published_at": "",
            "likes": 0,
            "comments": 0,
            "collections": 0,
            "shares": 0,
            "play_count": 0,
        }

        try:
            title = self.page.title()
            self.logger.info(f"[douyin] 详情页标题: {title}, URL: {self.page.url}")
        except Exception:
            title = ""

        # 从 meta description 提取内容、作者、点赞、发布时间
        try:
            meta_desc = self.page.query_selector('meta[name="description"]')
            desc = (meta_desc.get_attribute("content") or "").strip() if meta_desc else ""
            if desc and len(desc) > 10:
                data["content"] = desc.split("-")[0].strip()  # 取前面文案部分
                # 作者：XXX 于 2026XXXX 发布
                author_match = re.search(r"-\s*(.+?)\s*于\s*(\d{8})\s*发布", desc)
                if author_match:
                    data["author"] = author_match.group(1).strip()
                    data["published_at"] = author_match.group(2)
                # 点赞数：已经收获了 X 个喜欢
                like_match = re.search(r"收获了\s*(\d+\.?\d*[wW万]?)\s*个喜欢", desc)
                if like_match:
                    data["likes"] = parse_count(like_match.group(1))
        except Exception as e:
            self.logger.warning(f"[douyin] meta 描述解析失败: {e}")

        # 如果 meta 没拿到内容，从 title 兜底
        if not data["content"] and title and "-" in title:
            data["content"] = title.split("-")[0].strip()

        # 兜底：从 body 文本提取播放量
        try:
            page_text = self.page.inner_text("body")
            play_match = re.search(r"(\d+\.?\d*[wW万]?)[\s]*次播放", page_text)
            if play_match:
                data["play_count"] = parse_count(play_match.group(1))
        except Exception:
            pass

        self.logger.info(f"[douyin] 详情解析结果: 文案 {len(data['content'])} 字, 点赞 {data['likes']}, 评论 {data['comments']}, 收藏 {data['collections']}")
        return data

    def _pass_threshold(self, item: Dict[str, Any]) -> bool:
        """按阈值过滤"""
        for key, min_val in self.thresholds.items():
            if min_val and item.get(key, 0) < min_val:
                return False
        return True
