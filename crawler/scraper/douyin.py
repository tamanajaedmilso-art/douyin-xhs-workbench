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
        for card in results[:max_results]:
            try:
                detail = self.parse_detail(card["url"])
                card.update(detail)
                if self._pass_threshold(card):
                    card["keyword"] = keyword
                    card["platform"] = "douyin"
                    detailed.append(card)
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
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                if "/video/" not in href:
                    continue
                title_el = el.query_selector("span, .title, [class*='title']")
                title = title_el.inner_text() if title_el else ""
                cards.append({"url": href, "title": truncate_text(title, 200)})
            except Exception:
                continue
        return cards

    def parse_detail(self, url: str) -> Dict[str, Any]:
        """进入视频详情页采集完整信息"""
        if not self.safe_goto(url, wait_until="domcontentloaded"):
            return {}
        time.sleep(2)

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

        # 标题/文案（抖音详情页文案在 .desc 或 video-info 区域，可能变化）
        content_selectors = [
            '[data-e2e="video-desc"]',
            '.video-info-detail .desc',
            '.desc-info-text',
            '.title .desc',
            '[class*="desc"][class*="video"]',
        ]
        for sel in content_selectors:
            try:
                el = self.page.query_selector(sel)
                if el:
                    data["content"] = el.inner_text().strip()
                    break
            except Exception:
                continue

        # 作者
        author_selectors = [
            '[data-e2e="video-author-name"]',
            '.author-name',
            '.user-info .nickname',
        ]
        for sel in author_selectors:
            try:
                el = self.page.query_selector(sel)
                if el:
                    data["author"] = el.inner_text().strip()
                    break
            except Exception:
                continue

        # 互动数据：点赞、评论、收藏、分享、播放量
        stat_selectors = {
            "likes": [
                '[data-e2e="video-like-count"]',
                '.like-count',
                '[class*="like"] [class*="count"]',
            ],
            "comments": [
                '[data-e2e="video-comment-count"]',
                '.comment-count',
                '[class*="comment"] [class*="count"]',
            ],
            "collections": [
                '[data-e2e="video-collect-count"]',
                '.collect-count',
                '[class*="collect"] [class*="count"]',
            ],
            "shares": [
                '[data-e2e="video-share-count"]',
                '.share-count',
            ],
        }
        for key, selectors in stat_selectors.items():
            for sel in selectors:
                try:
                    el = self.page.query_selector(sel)
                    if el:
                        data[key] = parse_count(el.inner_text())
                        break
                except Exception:
                    continue

        # 发布时间
        time_selectors = [
            '[data-e2e="video-publish-time"]',
            '.publish-time',
            '[class*="publish"][class*="time"]',
        ]
        for sel in time_selectors:
            try:
                el = self.page.query_selector(sel)
                if el:
                    data["published_at"] = el.inner_text().strip()
                    break
            except Exception:
                continue

        # 播放量通常在搜索卡片上，详情页可能没有，尝试提取
        try:
            page_text = self.page.inner_text("body")
            play_match = re.search(r"(\d+\.?\d*[wW万]?)[\s]*次播放", page_text)
            if play_match:
                data["play_count"] = parse_count(play_match.group(1))
        except Exception:
            pass

        return data

    def _pass_threshold(self, item: Dict[str, Any]) -> bool:
        """按阈值过滤"""
        for key, min_val in self.thresholds.items():
            if min_val and item.get(key, 0) < min_val:
                return False
        return True
