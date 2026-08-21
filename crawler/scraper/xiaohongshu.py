import re
import time
from typing import Any, Dict, List

from utils import human_scroll, parse_count, truncate_text
from .base import BaseScraper


class XiaohongshuScraper(BaseScraper):
    """小红书爬虫（网页版）

    注意：小红书网页结构变化频繁，若采集失败请按实际页面调整 CSS 选择器。
    """

    BASE_URL = "https://www.xiaohongshu.com"

    def __init__(self, config: Dict[str, Any], logger):
        super().__init__("xiaohongshu", config, logger)
        self.thresholds = config.get("thresholds", {}).get("xiaohongshu", {})

    def search(self, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """按关键词搜索小红书笔记"""
        self.logger.info(f"[xiaohongshu] 开始搜索关键词: {keyword}")
        search_url = f"{self.BASE_URL}/search_result?keyword={keyword}&source=web_search_result_notes"
        if not self.safe_goto(search_url):
            return []

        time.sleep(3)
        self.wait_for_manual_login()

        results = []
        seen_urls = set()
        attempts = 0
        while len(results) < max_results and attempts < max_results // 3 + 5:
            cards = self._extract_note_cards()
            for card in cards:
                url = card.get("url", "")
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    results.append(card)
                if len(results) >= max_results:
                    break
            self.human_scroll(count=2)
            attempts += 1

        self.logger.info(f"[xiaohongshu] 关键词 [{keyword}] 搜索到 {len(results)} 条结果")

        detailed = []
        for card in results[:max_results]:
            try:
                detail = self.parse_detail(card["url"])
                card.update(detail)
                if self._pass_threshold(card):
                    card["keyword"] = keyword
                    card["platform"] = "xiaohongshu"
                    detailed.append(card)
                self.random_wait()
            except Exception as e:
                self.logger.error(f"[xiaohongshu] 详情页采集失败: {card.get('url')}, {e}")
        return detailed

    def _extract_note_cards(self) -> List[Dict[str, Any]]:
        """从搜索结果页提取笔记卡片"""
        cards = []
        selectors = [
            'a[href*="/explore/"]',
            'a[href*="/discovery/item/"]',
            '.note-item a',
            '[class*="note-item"] a',
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
                if not href:
                    continue
                if not href.startswith("http"):
                    href = self.BASE_URL + href
                if "/explore/" not in href and "/discovery/item/" not in href:
                    continue
                # 标题可能在 a 标签文字或父元素里
                title = el.inner_text().strip().split("\n")[0]
                cards.append({"url": href, "title": truncate_text(title, 200)})
            except Exception:
                continue
        return cards

    def parse_detail(self, url: str) -> Dict[str, Any]:
        """进入笔记详情页采集完整信息"""
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

        # 笔记正文
        content_selectors = [
            '#detail-desc',
            '.note-content',
            '.desc',
            '[class*="content"] [class*="desc"]',
            '.note-text',
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
            '.author-name',
            '.user-name',
            '[class*="author"] [class*="name"]',
            '.publisher-name',
        ]
        for sel in author_selectors:
            try:
                el = self.page.query_selector(sel)
                if el:
                    data["author"] = el.inner_text().strip()
                    break
            except Exception:
                continue

        # 互动数据
        stat_selectors = {
            "likes": [
                '.like-count',
                '.count[data-type="like"]',
                '[class*="like"] [class*="count"]',
            ],
            "comments": [
                '.comment-count',
                '.count[data-type="comment"]',
                '[class*="comment"] [class*="count"]',
            ],
            "collections": [
                '.collect-count',
                '.count[data-type="collect"]',
                '[class*="collect"] [class*="count"]',
            ],
            "shares": [
                '.share-count',
                '.count[data-type="share"]',
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
            '.publish-time',
            '.time',
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

        return data

    def _pass_threshold(self, item: Dict[str, Any]) -> bool:
        """按阈值过滤"""
        for key, min_val in self.thresholds.items():
            if min_val and item.get(key, 0) < min_val:
                return False
        return True
