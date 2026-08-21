#!/usr/bin/env python3
"""
抖音/小红书医美+试管婴儿爆款采集工具

用法：
    python main.py --run              # 手动执行一次采集
    python main.py --schedule         # 启动定时每周采集（默认周一 9:00）
    python main.py --export           # 导出已采集数据为 Excel/CSV
    python main.py --stats            # 查看采集统计
"""
import argparse
import os
import sys
import time
from datetime import datetime
from typing import Any, Dict, List

from analyzer import ContentAnalyzer
from exporter import Exporter
from scraper import DouyinScraper, XiaohongshuScraper
from storage import Storage
from sync import push_items, push_storage
from utils import ensure_dirs, load_config, now_str, setup_logging


def run_collection(config: Dict[str, Any], logger) -> List[Dict[str, Any]]:
    """执行一次完整采集，按关键词/平台增量保存，避免长任务超时丢失进度"""
    storage = Storage(config.get("data_dir", "./data"))
    analyzer = ContentAnalyzer()
    category_map = config.get("category_map", {})
    all_items: List[Dict[str, Any]] = []

    platforms = config.get("platforms", [])
    keywords = config.get("keywords", [])
    max_per_keyword = config.get("max_results_per_keyword", 20)

    def process_and_save(items: List[Dict[str, Any]], raw_kw: str, label: str):
        for item in items:
            item["category"] = category_map.get(raw_kw, "其他")
        analyzer.batch_analyze(items)
        added = storage.add_batch(items)
        storage.save()
        all_items.extend(items)
        logger.info(f"[save] {label} 采集 {len(items)} 条，新增 {added} 条，累计 {len(storage.items)} 条")

    if "douyin" in platforms:
        scraper = DouyinScraper(config, logger)
        try:
            scraper.start()
            for kw in keywords:
                try:
                    items = scraper.search(kw, max_results=max_per_keyword)
                    process_and_save(items, kw, f"抖音-{kw}")
                except Exception as e:
                    logger.error(f"[douyin] 关键词「{kw}」采集异常: {e}")
                    storage.save()
        finally:
            scraper.stop()

    if "xiaohongshu" in platforms:
        scraper = XiaohongshuScraper(config, logger)
        try:
            scraper.start()
            for kw in keywords:
                try:
                    items = scraper.search(kw, max_results=max_per_keyword)
                    process_and_save(items, kw, f"小红书-{kw}")
                except Exception as e:
                    logger.error(f"[xiaohongshu] 关键词「{kw}」采集异常: {e}")
                    storage.save()
        finally:
            scraper.stop()

    logger.info(f"本次采集完成：本次获取 {len(all_items)} 条，累计 {len(storage.items)} 条")

    # 自动同步到后端
    backend_cfg = config.get("backend", {})
    if backend_cfg.get("auto_sync") and all_items:
        if backend_cfg.get("url") and backend_cfg.get("api_key"):
            push_items(all_items, config, logger)
        else:
            logger.warning("[sync] auto_sync 已开启但 backend.url 或 api_key 未配置，跳过同步")

    return all_items


def export_data(config: Dict[str, Any], logger, fmt: str = "both") -> Dict[str, str]:
    """导出已采集数据"""
    storage = Storage(config.get("data_dir", "./data"))
    analyzer = ContentAnalyzer()
    items = analyzer.batch_analyze(storage.items)
    exporter = Exporter(config.get("output_dir", "./output"))
    paths = exporter.export_by_platform(items, fmt=fmt)
    for k, v in paths.items():
        if v:
            logger.info(f"已导出 {k.upper()}: {v}")
    return paths


def show_stats(config: Dict[str, Any], logger) -> None:
    """显示采集统计"""
    storage = Storage(config.get("data_dir", "./data"))
    stats = storage.stats()
    logger.info(f"采集统计：总计 {stats['total']} 条 | 抖音 {stats['douyin']} 条 | 小红书 {stats['xiaohongshu']} 条")


def run_login_only(config: Dict[str, Any], logger) -> None:
    """只打开浏览器并等待登录，用于首次获取登录态"""
    platforms = config.get("platforms", [])
    if "douyin" in platforms:
        scraper = DouyinScraper(config, logger)
        try:
            scraper.start()
            scraper.safe_goto("https://www.douyin.com", wait_until="domcontentloaded")
            logger.info("[login] 抖音已打开，请手动登录，完成后按回车...")
            try:
                input("按回车继续...")
            except EOFError:
                logger.warning("非交互式环境，等待 600 秒，请尽快完成登录...")
                time.sleep(600)
        finally:
            scraper.stop()

    if "xiaohongshu" in platforms:
        scraper = XiaohongshuScraper(config, logger)
        try:
            scraper.start()
            scraper.safe_goto("https://www.xiaohongshu.com", wait_until="domcontentloaded")
            logger.info("[login] 小红书已打开，请手动登录，完成后按回车...")
            try:
                input("按回车继续...")
            except EOFError:
                logger.warning("非交互式环境，等待 600 秒，请尽快完成登录...")
                time.sleep(600)
        finally:
            scraper.stop()

    logger.info("[login] 登录态已保存，可以运行 python main.py --run 开始采集")


def run_scheduler(config: Dict[str, Any], logger) -> None:
    """启动定时任务"""
    try:
        import schedule
    except ImportError:
        logger.error("定时任务需要 schedule 库，请运行: pip install schedule")
        return

    sched = config.get("schedule", {})
    day = sched.get("day_of_week", "mon").lower()
    hour = sched.get("hour", 9)
    minute = sched.get("minute", 0)

    days = {
        "mon": schedule.every().monday,
        "tue": schedule.every().tuesday,
        "wed": schedule.every().wednesday,
        "thu": schedule.every().thursday,
        "fri": schedule.every().friday,
        "sat": schedule.every().saturday,
        "sun": schedule.every().sunday,
    }
    job = days.get(day, schedule.every().monday)
    job.at(f"{hour:02d}:{minute:02d}").do(lambda: run_collection(config, logger))

    logger.info(f"定时任务已启动：每周 {day} {hour:02d}:{minute:02d} 执行采集")
    while True:
        schedule.run_pending()
        time.sleep(60)


def main():
    parser = argparse.ArgumentParser(description="抖音/小红书爆款内容采集工具")
    parser.add_argument("--run", action="store_true", help="手动执行一次采集")
    parser.add_argument("--login", action="store_true", help="只打开浏览器保存登录态")
    parser.add_argument("--export", action="store_true", help="导出已采集数据")
    parser.add_argument("--stats", action="store_true", help="查看采集统计")
    parser.add_argument("--schedule", action="store_true", help="启动定时每周采集")
    parser.add_argument("--sync-only", action="store_true", help="只把本地已采集数据同步到后端")
    parser.add_argument("--format", choices=["csv", "xlsx", "both"], default="both", help="导出格式")
    parser.add_argument("--config", default="config.json", help="配置文件路径")
    args = parser.parse_args()

    if not os.path.exists(args.config):
        print(f"配置文件不存在: {args.config}")
        sys.exit(1)

    config = load_config(args.config)
    ensure_dirs([
        config.get("cookies_dir", "./cookies"),
        config.get("data_dir", "./data"),
        config.get("output_dir", "./output"),
        config.get("user_data_dir", "./browser_profile"),
    ])
    logger = setup_logging("INFO")

    # 环境检查
    if config.get("headless") and not os.environ.get("DISPLAY"):
        logger.warning(
            "当前设置为 headless 模式且未检测到 DISPLAY 环境变量，"
            "若运行失败请将 config.json 中的 headless 改为 false，并在带桌面的电脑上执行。"
        )

    if args.run:
        items = run_collection(config, logger)
        export_data(config, logger, fmt=args.format)
    elif args.login:
        run_login_only(config, logger)
    elif args.export:
        export_data(config, logger, fmt=args.format)
    elif args.stats:
        show_stats(config, logger)
    elif args.schedule:
        run_scheduler(config, logger)
    elif args.sync_only:
        storage = Storage(config.get("data_dir", "./data"))
        push_storage(storage, config, logger)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
