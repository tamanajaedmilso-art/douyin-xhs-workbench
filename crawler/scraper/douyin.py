import re
import time
from datetime import datetime, timedelta
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
        self.category_map = config.get("category_map", {})
        self.category_rules = config.get("category_rules", {})

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
        category = self.category_map.get(keyword, "其他")
        for i, card in enumerate(results[:max_results]):
            try:
                self.logger.info(f"[douyin] 正在采集第 {i+1}/{len(results[:max_results])} 条详情: {card.get('url')}")
                detail = self.parse_detail(card["url"])
                card.update(detail)
                if self._pass_threshold(card, category):
                    card["keyword"] = keyword
                    card["platform"] = "douyin"
                    detailed.append(card)
                    self.logger.info(f"[douyin] 采集成功: {card.get('title', '')[:30]}，点赞 {card.get('likes', 0)}")
                else:
                    self.logger.info(f"[douyin] 未通过类目规则过滤: {card.get('title', '')[:30]}")
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

        # 提取评论文本（用于医美类精准评论过滤）
        data["comments_text"] = self._extract_comments()

        self.logger.info(f"[douyin] 详情解析结果: 文案 {len(data['content'])} 字, 点赞 {data['likes']}, 评论 {data['comments']}, 收藏 {data['collections']}, 抓取评论 {len(data['comments_text'])}")
        return data

    def _extract_comments(self, max_comments: int = 20) -> List[str]:
        """滚动评论区，抓取前 N 条评论文本"""
        comments = []
        try:
            # 尝试多种评论文本选择器
            selectors = [
                '[data-e2e="comment-list"] span',
                '[class*="comment"] [class*="text"] span',
                '[class*="comment"] span',
                '.comment-mainContent span',
                'div[role="listitem"] span',
            ]
            # 先滚动几次加载评论
            for _ in range(3):
                self.human_scroll(count=2)
                time.sleep(1)

            for sel in selectors:
                try:
                    elements = self.page.query_selector_all(sel)
                    for el in elements:
                        text = (el.inner_text() or "").strip()
                        if text and len(text) > 2 and text not in comments:
                            comments.append(text)
                        if len(comments) >= max_comments:
                            break
                    if comments:
                        break
                except Exception:
                    continue
        except Exception as e:
            self.logger.warning(f"[douyin] 评论抓取失败: {e}")
        return comments[:max_comments]

    def _pass_threshold(self, item: Dict[str, Any], category: str = "其他") -> bool:
        """按类目规则过滤。先检查全局阈值，再检查类目特殊规则。"""
        # 全局阈值
        key_map = {
            "likes_min": "likes",
            "comments_min": "comments",
            "collections_min": "collections",
            "shares_min": "shares",
            "play_count_min": "play_count",
        }
        for threshold_key, min_val in self.thresholds.items():
            item_key = key_map.get(threshold_key, threshold_key)
            if min_val and item.get(item_key, 0) < min_val:
                return False

        rules = self.category_rules.get(category, {})
        if not rules:
            return True

        # 类目点赞阈值
        likes_min = rules.get("likes_min")
        if likes_min and item.get("likes", 0) < likes_min:
            return False

        # 发布时间限制（试管婴儿：6 个月内）
        max_age_days = rules.get("max_age_days")
        if max_age_days:
            published_at = item.get("published_at", "")
            if not self._within_days(published_at, max_age_days):
                self.logger.info(f"[douyin] 未通过发布时间过滤: {published_at}, 要求 {max_age_days} 天内")
                return False

        # 标题/文案负面关键词排除（医美：过滤引流爆款，排除负面内容）
        exclude_title_keywords = rules.get("exclude_title_keywords", [])
        if exclude_title_keywords:
            text_to_check = f"{item.get('title', '')} {item.get('content', '')}"
            matched_negative = [kw for kw in exclude_title_keywords if kw in text_to_check]
            if matched_negative:
                self.logger.info(f"[douyin] 未通过负面关键词过滤: 命中 {matched_negative}")
                return False

        # 评论关键词过滤（医美：评论区含精准关键词）
        comment_keywords = rules.get("comment_keywords", [])
        if comment_keywords:
            comments_text = item.get("comments_text", [])
            joined = " ".join(comments_text)
            matched = [kw for kw in comment_keywords if kw in joined]
            if not matched:
                self.logger.info(f"[douyin] 未通过评论关键词过滤: 评论中未找到 {comment_keywords}")
                return False
            item["matched_comment_keywords"] = matched

        return True

    def _within_days(self, published_at: str, days: int) -> bool:
        """判断发布时间是否在 N 天内。published_at 格式如 20260820"""
        if not published_at:
            return False
        try:
            pub_date = datetime.strptime(str(published_at), "%Y%m%d")
            cutoff = datetime.now() - timedelta(days=days)
            return pub_date >= cutoff
        except ValueError:
            # 尝试 ISO 格式
            try:
                pub_date = datetime.fromisoformat(str(published_at).replace("Z", "+00:00"))
                cutoff = datetime.now(pub_date.tzinfo) - timedelta(days=days)
                return pub_date >= cutoff
            except Exception:
                return False
