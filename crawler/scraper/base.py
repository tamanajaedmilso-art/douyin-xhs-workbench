import json
import os
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from playwright.sync_api import Page, sync_playwright

from utils import ensure_dirs, random_delay


class BaseScraper(ABC):
    """爬虫基类：浏览器管理、Cookie、通用工具"""

    def __init__(self, platform: str, config: Dict[str, Any], logger):
        self.platform = platform
        self.config = config
        self.logger = logger
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None
        self.cookies_path = Path(config.get("cookies_dir", "./cookies")) / f"{platform}_cookies.json"
        ensure_dirs([config.get("cookies_dir", "./cookies")])

    def _build_launch_options(self) -> Dict[str, Any]:
        """启动浏览器参数，带基础反检测"""
        opts = {
            "headless": self.config.get("headless", False),
            "args": [
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                f"--window-size={self.config['browser']['viewport_width']},{self.config['browser']['viewport_height']}",
            ],
        }
        return opts

    def start(self) -> None:
        """启动浏览器"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(**self._build_launch_options())
        self.context = self.browser.new_context(
            viewport={
                "width": self.config["browser"]["viewport_width"],
                "height": self.config["browser"]["viewport_height"],
            },
            user_agent=self.config["browser"].get("user_agent"),
            locale=self.config["browser"].get("locale", "zh-CN"),
            timezone_id="Asia/Shanghai",
        )
        # 注入脚本隐藏 webdriver 痕迹
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.chrome = { runtime: {} };
        """)
        self.page = self.context.new_page()
        self._load_cookies()

    def stop(self) -> None:
        """关闭浏览器并保存 Cookie"""
        if self.context and self.page:
            self._save_cookies()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def _load_cookies(self) -> None:
        """加载本地 Cookie"""
        if self.cookies_path.exists():
            with open(self.cookies_path, "r", encoding="utf-8") as f:
                cookies = json.load(f)
            self.context.add_cookies(cookies)
            self.logger.info(f"[{self.platform}] 已加载 Cookie")

    def _save_cookies(self) -> None:
        """保存 Cookie 到本地"""
        cookies = self.context.cookies()
        with open(self.cookies_path, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        self.logger.info(f"[{self.platform}] 已保存 Cookie")

    def safe_goto(self, url: str, wait_until: str = "networkidle", timeout: int = 30000) -> bool:
        """安全跳转页面，失败返回 False"""
        try:
            self.page.goto(url, wait_until=wait_until, timeout=timeout)
            return True
        except Exception as e:
            self.logger.error(f"[{self.platform}] 访问失败: {url}, 错误: {e}")
            return False

    def random_wait(self) -> None:
        """按配置随机等待"""
        delay = self.config.get("delay", {})
        random_delay(delay.get("min_seconds", 2), delay.get("max_seconds", 5))

    def human_scroll(self, count: int = 3) -> None:
        """人类式滚动"""
        delay = self.config.get("delay", {})
        for _ in range(count):
            distance = random.randint(400, 1000)
            self.page.evaluate(f"window.scrollBy(0, {distance})")
            random_delay(delay.get("scroll_pause_min", 1), delay.get("scroll_pause_max", 2))

    def is_login_page(self) -> bool:
        """检测当前是否在登录页，子类可覆盖"""
        url = self.page.url
        return "login" in url.lower() or "signin" in url.lower()

    @abstractmethod
    def search(self, keyword: str, max_results: int = 20) -> List[Dict[str, Any]]:
        """搜索关键词并返回作品列表，子类必须实现"""
        pass

    @abstractmethod
    def parse_detail(self, url: str) -> Dict[str, Any]:
        """进入作品详情页采集完整信息，子类必须实现"""
        pass
